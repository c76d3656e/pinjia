#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
露天台阶爆破效果综合评价系统 - 演示版本
使用Flask框架实现基本功能演示

作者: 系统开发团队
版本: 1.0.0
创建时间: 2024-01-XX
"""

import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
from typing import Dict, List, Any, Optional
try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("警告: pyngrok未安装，无法使用ngrok功能")

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 创建Flask应用
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
CORS(app)

# 全局变量存储应用状态
app_state = {
    'indicators': [],
    'selected_indicators': [],
    'weights': {},
    'ranges': {},
    'measured_values': {},
    'evaluation_result': None
}

def load_indicators():
    """加载指标数据"""
    try:
        indicators_file = Path('config/indicators.json')
        print(f"[DEBUG] 检查指标文件: {indicators_file}")
        print(f"[DEBUG] 文件是否存在: {indicators_file.exists()}")
        
        if indicators_file.exists():
            with open(indicators_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[DEBUG] 原始数据结构: {list(data.keys())}")
                
                # 检查数据结构
                if 'categories' in data:
                    # 新的分类结构
                    all_indicators = []
                    for category in data['categories']:
                        category_indicators = category.get('indicators', [])
                        print(f"[DEBUG] 分类 '{category.get('name', '')}' 包含 {len(category_indicators)} 个指标")
                        all_indicators.extend(category_indicators)
                    app_state['indicators'] = all_indicators
                    print(f"[DEBUG] 总共加载了 {len(all_indicators)} 个指标")
                elif 'indicators' in data:
                    # 旧的直接结构
                    app_state['indicators'] = data.get('indicators', [])
                    print(f"[DEBUG] 直接加载了 {len(app_state['indicators'])} 个指标")
                else:
                    print(f"[ERROR] 未找到有效的指标数据结构")
                    return False
                    
                # 打印前几个指标用于验证
                for i, indicator in enumerate(app_state['indicators'][:3]):
                    print(f"[DEBUG] 指标 {i+1}: {indicator.get('name', 'Unknown')} (ID: {indicator.get('id', 'Unknown')})")
                    
                return True
        else:
            print(f"[ERROR] 指标文件不存在: {indicators_file}")
    except Exception as e:
        print(f"[ERROR] 加载指标失败: {e}")
        import traceback
        traceback.print_exc()
    return False

def calculate_fahp_weights(matrix: List[List[float]]) -> Optional[List[float]]:
    """计算FAHP模糊层次分析法权重（模糊互补判断矩阵）"""
    try:
        matrix = np.array(matrix, dtype=float)
        n = matrix.shape[0]
        
        print(f"输入矩阵: {matrix}")

        if matrix.shape != (n, n) or n == 0:
            raise ValueError("判断矩阵必须为非空方阵")

        if n == 1:
            if abs(matrix[0][0] - 0.5) > 1e-6:
                print(f"警告: 单指标矩阵对角线元素应为0.5，但matrix[0][0] = {matrix[0][0]}")
            return [1.0], 0.0
        
        # 验证矩阵是否为模糊互补判断矩阵
        for i in range(n):
            for j in range(n):
                if matrix[i][j] < 0 or matrix[i][j] > 1:
                    raise ValueError(f"FAHP判断矩阵元素必须在0-1之间: matrix[{i}][{j}] = {matrix[i][j]}")
                if i == j and abs(matrix[i][j] - 0.5) > 1e-6:
                    print(f"警告: 对角线元素应为0.5，但matrix[{i}][{j}] = {matrix[i][j]}")
                    matrix[i][j] = 0.5
                elif i != j and abs(matrix[i][j] + matrix[j][i] - 1.0) > 1e-6:
                    raise ValueError(
                        f"FAHP判断矩阵不满足互补性: "
                        f"matrix[{i}][{j}] + matrix[{j}][{i}] = {matrix[i][j] + matrix[j][i]}"
                    )
        
        # 步骤1：计算行和
        row_sums = np.sum(matrix, axis=1)
        print(f"行和: {row_sums}")
        
        # 步骤2：计算权重向量
        # wi = (Σrij + n / 2 - 1) / (n * (n - 1))
        weights = (row_sums + n / 2 - 1) / (n * (n - 1))
        total_weight = np.sum(weights)
        if np.any(weights < -1e-10) or abs(total_weight - 1.0) > 1e-6:
            raise ValueError(f"FAHP权重计算异常: weights={weights}, sum={total_weight}")
        weights = np.clip(weights, 0, None)
        weights = weights / np.sum(weights)
        print(f"权重: {weights}")
        
        # 步骤4：一致性检验
        ci = calculate_fahp_consistency(matrix, weights)
        
        print(f"FAHP权重计算完成: weights={weights}, CI={ci}")
        
        return weights.tolist(), ci
    except Exception as e:
        print(f"FAHP权重计算错误: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def calculate_fahp_consistency(matrix: np.ndarray, weights: np.ndarray) -> float:
    """计算FAHP一致性指标 - 基于相容性指标I(A,W*)"""
    try:
        n = matrix.shape[0]
        if n <= 1:
            return 0.0
        
        # 计算特征矩阵W*
        # W*ij = wi / (wi + wj)
        W_star = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                denominator = weights[i] + weights[j]
                W_star[i][j] = weights[i] / denominator if denominator > 0 else 0.5
        
        print(f"特征矩阵W*: {W_star}")
        
        # 计算相容性指标I(A,W*)
        # I(A,W*) = (1/n^2) * Σ|aij + w*ji - 1|，等价于Σ|aij - w*ij|。
        diff_matrix = np.abs(matrix + W_star.T - 1)
        consistency_index = np.sum(diff_matrix) / (n * n)
        
        print(f"差异矩阵: {diff_matrix}")
        print(f"相容性指标I(A,W*): {consistency_index}")
        
        return consistency_index
    except Exception as e:
        print(f"一致性计算错误: {e}")
        import traceback
        traceback.print_exc()
        return 1.0

def calculate_ahp_weights(matrix: List[List[float]]) -> Optional[List[float]]:
    """计算AHP权重"""
    try:
        matrix = np.array(matrix, dtype=float)
        n = matrix.shape[0]

        if matrix.shape != (n, n) or n == 0:
            raise ValueError("AHP判断矩阵必须为非空方阵")

        if np.any(matrix <= 0):
            raise ValueError("AHP判断矩阵元素必须为正数")

        if not np.allclose(np.diag(matrix), 1.0, atol=1e-6):
            raise ValueError("AHP判断矩阵对角线元素必须为1")

        if not np.allclose(matrix * matrix.T, np.ones((n, n)), atol=1e-3):
            raise ValueError("AHP判断矩阵必须满足互反性 aij * aji = 1")

        if n == 1:
            return [1.0]
        
        # 计算特征向量
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_eigenvalue_index = np.argmax(eigenvalues.real)
        principal_eigenvector = eigenvectors[:, max_eigenvalue_index].real

        if np.sum(principal_eigenvector) < 0:
            principal_eigenvector = -principal_eigenvector
        if np.any(principal_eigenvector <= 0):
            principal_eigenvector = np.abs(principal_eigenvector)
        
        # 归一化权重
        weights = principal_eigenvector / np.sum(principal_eigenvector)
        
        # 一致性检查
        max_eigenvalue = eigenvalues[max_eigenvalue_index].real
        ci = (max_eigenvalue - n) / (n - 1)
        ri_values = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
        ri = ri_values.get(n, 1.45)
        cr = ci / ri if ri > 0 else 0
        
        if cr > 0.1:
            raise ValueError(f"AHP判断矩阵一致性不满足要求，CR = {cr:.3f} > 0.1")
        
        return weights.tolist()
    except Exception as e:
        print(f"AHP权重计算失败: {e}")
        return None

def calculate_entropy_weights(
    data_matrix: List[List[float]],
    indicator_ids: List[str],
    benefit_flags: List[bool]
) -> Optional[Dict[str, float]]:
    """使用熵权法计算权重"""
    try:
        matrix = np.array(data_matrix, dtype=float)
        if matrix.ndim != 2:
            raise ValueError("熵权法数据矩阵必须为二维数组")
        if matrix.shape[1] != len(indicator_ids):
            raise ValueError("数据矩阵列数必须与指标数量一致")
        if matrix.shape[0] < 2:
            raise ValueError("熵权法至少需要2个样本")
        if len(benefit_flags) != len(indicator_ids):
            raise ValueError("指标方向数量必须与指标数量一致")
        if not np.all(np.isfinite(matrix)):
            raise ValueError("数据矩阵包含无效数值")

        normalized = np.zeros_like(matrix, dtype=float)
        for j in range(matrix.shape[1]):
            column = matrix[:, j]
            col_min = np.min(column)
            col_max = np.max(column)
            if abs(col_max - col_min) < 1e-12:
                normalized[:, j] = 1.0
            elif benefit_flags[j]:
                normalized[:, j] = (column - col_min) / (col_max - col_min)
            else:
                normalized[:, j] = (col_max - column) / (col_max - col_min)

        column_sums = np.sum(normalized, axis=0)
        p_matrix = np.zeros_like(normalized, dtype=float)
        for j, column_sum in enumerate(column_sums):
            if column_sum > 0:
                p_matrix[:, j] = normalized[:, j] / column_sum
            else:
                p_matrix[:, j] = 1.0 / matrix.shape[0]

        entropy = np.zeros(matrix.shape[1])
        for j in range(matrix.shape[1]):
            p = p_matrix[:, j]
            p = p[p > 0]
            entropy[j] = -np.sum(p * np.log(p)) / np.log(matrix.shape[0])

        diversity = 1 - entropy
        diversity_sum = np.sum(diversity)
        if diversity_sum <= 1e-12:
            weights = np.full(len(indicator_ids), 1.0 / len(indicator_ids))
        else:
            weights = diversity / diversity_sum

        return dict(zip(indicator_ids, weights.tolist()))
    except Exception as e:
        print(f"熵权法权重计算失败: {e}")
        return None

def calculate_indicator_score_new(value: float, range_data: dict) -> tuple:
    """根据新的五级评价标准计算指标得分和等级，支持插值计算"""
    try:
        # 定义等级分数
        excellent_score = 100.0
        good_score = 85.0
        average_score = 70.0
        poor_score = 50.0
        verypoor_score = 20.0
        
        # 获取各等级范围
        excellent = range_data.get('excellent', {})
        good = range_data.get('good', {})
        average = range_data.get('average', {})
        poor = range_data.get('poor', {})
        verypoor = range_data.get('verypoor', {})
        
        excellent_val = excellent.get('value', 0)
        good_min = good.get('min', 0)
        good_max = good.get('max', 0)
        avg_min = average.get('min', 0)
        avg_max = average.get('max', 0)
        poor_min = poor.get('min', 0)
        poor_max = poor.get('max', 0)
        verypoor_val = verypoor.get('value', 0)
        
        lower_is_better = excellent.get('operator') == '≤'

        def interpolate(x, x1, x2, y1, y2):
            if abs(x2 - x1) < 1e-12:
                return y1
            ratio = (x - x1) / (x2 - x1)
            return y1 + ratio * (y2 - y1)

        if lower_is_better:
            if value <= excellent_val:
                return excellent_score, '优'
            if value >= verypoor_val:
                return verypoor_score, '很差'
            if good_min <= value <= good_max:
                return interpolate(value, good_min, good_max, excellent_score, good_score), '良'
            if avg_min <= value <= avg_max:
                return interpolate(value, avg_min, avg_max, good_score, average_score), '一般'
            if poor_min <= value <= poor_max:
                return interpolate(value, poor_min, poor_max, average_score, poor_score), '较差'
            if good_max < value < avg_min:
                return interpolate(value, good_max, avg_min, good_score, average_score), '一般'
            if avg_max < value < poor_min:
                return interpolate(value, avg_max, poor_min, average_score, poor_score), '较差'
            if poor_max < value < verypoor_val:
                return interpolate(value, poor_max, verypoor_val, poor_score, verypoor_score), '较差'
        else:
            if value >= excellent_val:
                return excellent_score, '优'
            if value <= verypoor_val:
                return verypoor_score, '很差'
            if good_min <= value <= good_max:
                return interpolate(value, good_min, good_max, good_score, excellent_score), '良'
            if avg_min <= value <= avg_max:
                return interpolate(value, avg_min, avg_max, average_score, good_score), '一般'
            if poor_min <= value <= poor_max:
                return interpolate(value, poor_min, poor_max, poor_score, average_score), '较差'
            if verypoor_val < value < poor_min:
                return interpolate(value, verypoor_val, poor_min, verypoor_score, poor_score), '较差'
            if poor_max < value < avg_min:
                return interpolate(value, poor_max, avg_min, average_score, average_score), '一般'
            if avg_max < value < good_min:
                return interpolate(value, avg_max, good_min, good_score, good_score), '良'

        return poor_score, '较差'
    except Exception as e:
        print(f"[ERROR] 计算指标得分时出错: {e}")
        return 50.0, '较差'

def calculate_indicator_score(value: float, optimal: float, worst: float, is_positive: bool = True) -> float:
    """计算单个指标得分（兼容旧版本）"""
    try:
        if is_positive:
            # 正向指标：值越大越好
            if worst >= optimal:
                return 0.0
            score = (value - worst) / (optimal - worst) * 100
        else:
            # 反向指标：值越小越好
            if optimal >= worst:
                return 0.0
            score = (worst - value) / (worst - optimal) * 100
        
        return max(0.0, min(100.0, score))
    except:
        return 0.0

def get_grade_from_score(score: float) -> str:
    """根据得分获取等级"""
    if score >= 90:
        return "优"
    elif score >= 80:
        return "良"
    elif score >= 70:
        return "一般"
    elif score >= 50:
        return "较差"
    else:
        return "很差"

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/indicators')
def get_indicators():
    """获取所有指标"""
    print(f"[DEBUG] API请求 /api/indicators")
    print(f"[DEBUG] 当前指标数量: {len(app_state['indicators'])}")
    
    if app_state['indicators']:
        print(f"[DEBUG] 返回指标列表，前3个指标:")
        for i, indicator in enumerate(app_state['indicators'][:3]):
            print(f"[DEBUG]   {i+1}. {indicator.get('name', 'Unknown')}")
    else:
        print(f"[DEBUG] 指标列表为空!")
    
    # 重新读取原始分类数据
    try:
        import json
        indicators_file = os.path.join('config', 'indicators.json')
        with open(indicators_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
            categories = original_data.get('categories', [])
    except Exception as e:
        print(f"[ERROR] 读取分类数据失败: {e}")
        categories = []
    
    return jsonify({
        'success': True,
        'data': app_state['indicators'],
        'categories': categories
    })

@app.route('/api/indicators/select', methods=['POST'])
def select_indicators():
    """选择指标"""
    try:
        data = request.get_json()
        selected_ids = data.get('indicator_ids', [])
        
        app_state['selected_indicators'] = [
            indicator for indicator in app_state['indicators']
            if indicator['id'] in selected_ids
        ]
        
        return jsonify({
            'success': True,
            'message': f'已选择 {len(app_state["selected_indicators"])} 个指标'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'选择指标失败: {str(e)}'
        })

@app.route('/api/weights/calculate', methods=['POST'])
def calculate_weights():
    """计算权重"""
    try:
        data = request.get_json()
        method = data.get('method', 'equal')
        
        if not app_state['selected_indicators']:
            return jsonify({
                'success': False,
                'message': '请先选择指标'
            })
        
        n = len(app_state['selected_indicators'])
        
        if method == 'equal':
            # 等权重
            weight_value = 1.0 / n
            weights = {indicator['id']: weight_value for indicator in app_state['selected_indicators']}
        
        elif method == 'expert':
            # 专家打分
            scores = data.get('scores', {})
            total_score = sum(scores.values())
            if total_score == 0:
                return jsonify({
                    'success': False,
                    'message': '专家打分总分不能为0'
                })
            weights = {id: score / total_score for id, score in scores.items()}
        
        elif method == 'ahp':
            # AHP层次分析法
            matrix = data.get('matrix', [])
            if len(matrix) != n or any(len(row) != n for row in matrix):
                return jsonify({
                    'success': False,
                    'message': f'判断矩阵维度应为 {n}x{n}'
                })
            
            weight_values = calculate_ahp_weights(matrix)
            if weight_values is None:
                return jsonify({
                    'success': False,
                    'message': 'AHP权重计算失败'
                })
            
            weights = {
                app_state['selected_indicators'][i]['id']: weight_values[i]
                for i in range(n)
            }

        elif method == 'entropy':
            data_matrix = data.get('data_matrix')
            if not data_matrix:
                return jsonify({
                    'success': False,
                    'message': '熵权法需要提供真实样本数据矩阵'
                })

            indicator_ids = [indicator['id'] for indicator in app_state['selected_indicators']]
            benefit_flags = [
                bool(indicator.get('is_positive', True))
                for indicator in app_state['selected_indicators']
            ]
            weights = calculate_entropy_weights(data_matrix, indicator_ids, benefit_flags)
            if weights is None:
                return jsonify({
                    'success': False,
                    'message': '熵权法权重计算失败'
                })
             
        elif method == 'fahp':
            # FAHP模糊层次分析法
            level1_matrix = data.get('level1_matrix', [])
            level2_matrices = data.get('level2_matrices', {})
            
            # 计算一级指标权重
            n = len(level1_matrix)
            if n < 2 or any(len(row) != n for row in level1_matrix):
                return jsonify({
                    'success': False,
                    'message': f'一级指标判断矩阵维度应为 {n}x{n}，且至少需要2个指标'
                })
            
            level1_weights, level1_ci = calculate_fahp_weights(level1_matrix)
            if level1_weights is None:
                return jsonify({
                    'success': False,
                    'message': 'FAHP一级指标权重计算失败'
                })
            
            # 计算二级指标权重并合成最终权重
            final_weights = {}
            
            category_order = ['technical', 'safety', 'economic']
            categories = data.get('level1_categories') or [
                category for category in category_order
                if any(ind['id'].startswith(category) for ind in app_state['selected_indicators'])
            ]
            categories = [
                category for category in categories
                if category in category_order
                and any(ind['id'].startswith(category) for ind in app_state['selected_indicators'])
            ]

            if len(categories) != len(level1_weights):
                return jsonify({
                    'success': False,
                    'message': '一级指标分类数量与一级权重数量不一致'
                })
            
            for i, category in enumerate(categories):
                if category in level2_matrices:
                    level2_matrix = level2_matrices[category]
                    level2_weights, level2_ci = calculate_fahp_weights(level2_matrix)
                    
                    if level2_weights is None:
                        return jsonify({
                            'success': False,
                            'message': f'{category}类别二级指标权重计算失败'
                        })
                    
                    # 获取该类别下的指标
                    category_indicators = [ind for ind in app_state['selected_indicators'] 
                                         if ind['id'].startswith(category)]
                    
                    # 计算最终权重（一级权重 × 二级权重）
                    for j, indicator in enumerate(category_indicators):
                        if j < len(level2_weights):
                            final_weights[indicator['id']] = level1_weights[i] * level2_weights[j]
            
            total_weight = sum(final_weights.values())
            if abs(total_weight - 1.0) > 1e-6:
                print(f"警告: FAHP综合权重和为 {total_weight}，执行数值归一化")
                final_weights = {k: v / total_weight for k, v in final_weights.items()}
            
            weights = final_weights
        
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的权重计算方法: {method}'
            })
        
        app_state['weights'] = weights
        
        return jsonify({
            'success': True,
            'data': weights,
            'message': '权重计算完成'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'权重计算失败: {str(e)}'
        })

@app.route('/api/weights/fahp/level1', methods=['POST'])
def calculate_fahp_level1():
    """计算FAHP一级指标权重"""
    try:
        data = request.get_json()
        matrix = data.get('matrix', [])
        
        n = len(matrix)
        if n < 2 or any(len(row) != n for row in matrix):
            return jsonify({
                'success': False,
                'message': f'一级指标判断矩阵维度应为 {n}x{n}，且至少需要2个指标'
            })
        
        weights, ci = calculate_fahp_weights(matrix)
        if weights is None:
            return jsonify({
                'success': False,
                'message': 'FAHP一级指标权重计算失败'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'weights': weights,
                'ci': ci,
                'matrix': matrix
            },
            'message': 'FAHP一级指标权重计算完成'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'FAHP一级指标权重计算失败: {str(e)}'
        })

@app.route('/api/weights/fahp/level2', methods=['POST'])
def calculate_fahp_level2():
    """计算FAHP二级指标权重"""
    try:
        data = request.get_json()
        category = data.get('category', '')
        matrix = data.get('matrix', [])
        indicators = data.get('indicators', [])
        
        n = len(matrix)
        if n == 0 or any(len(row) != n for row in matrix):
            return jsonify({
                'success': False,
                'message': f'二级指标判断矩阵维度不正确'
            })
        
        weights, ci = calculate_fahp_weights(matrix)
        if weights is None:
            return jsonify({
                'success': False,
                'message': f'{category}类别二级指标权重计算失败'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'category': category,
                'weights': weights,
                'ci': ci,
                'indicators': indicators
            },
            'message': f'{category}类别二级指标权重计算完成'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'FAHP二级指标权重计算失败: {str(e)}'
        })

@app.route('/api/ranges/set', methods=['POST'])
def set_ranges():
    """设置指标范围"""
    try:
        data = request.get_json()
        print(f"[DEBUG] 接收到范围设置请求: {data}")
        
        ranges = data.get('ranges', {})
        print(f"[DEBUG] 解析的范围数据: {ranges}")
        print(f"[DEBUG] 范围数据类型: {type(ranges)}")
        print(f"[DEBUG] 范围数据键数量: {len(ranges)}")
        
        app_state['ranges'] = ranges
        print(f"[DEBUG] 已保存到app_state['ranges']: {app_state['ranges']}")
        
        return jsonify({
            'success': True,
            'message': '指标范围设置完成'
        })
    except Exception as e:
        print(f"[ERROR] 设置范围失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'设置范围失败: {str(e)}'
        })

@app.route('/api/values/set', methods=['POST'])
def set_measured_values():
    """设置实测值"""
    try:
        data = request.get_json()
        values = data.get('values', {})
        
        app_state['measured_values'] = values
        
        return jsonify({
            'success': True,
            'message': '实测值设置完成'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'设置实测值失败: {str(e)}'
        })

@app.route('/api/data/submit', methods=['POST'])
def submit_data():
    """提交实测数据"""
    try:
        data = request.get_json()
        measured_values = data.get('measured_values', {})
        
        # 验证数据
        if not measured_values:
            return jsonify({
                'success': False,
                'message': '请输入实测数据'
            })
        
        # 检查是否所有选中的指标都有数据
        missing_indicators = []
        for indicator in app_state['selected_indicators']:
            if indicator['id'] not in measured_values:
                missing_indicators.append(indicator['name'])
        
        if missing_indicators:
            return jsonify({
                'success': False,
                'message': f'缺少以下指标的实测数据: {", ".join(missing_indicators)}'
            })
        
        # 保存实测数据
        app_state['measured_values'] = measured_values
        
        return jsonify({
            'success': True,
            'message': '实测数据提交成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交实测数据失败: {str(e)}'
        })

@app.route('/api/evaluation/calculate', methods=['POST'])
def calculate_evaluation():
    """执行综合评价"""
    try:
        print(f"[DEBUG] 开始综合评价计算")
        print(f"[DEBUG] app_state['selected_indicators']: {app_state['selected_indicators']}")
        print(f"[DEBUG] app_state['weights']: {app_state['weights']}")
        print(f"[DEBUG] app_state['ranges']: {app_state['ranges']}")
        print(f"[DEBUG] app_state['measured_values']: {app_state['measured_values']}")
        
        # 检查数据完整性
        if not app_state['selected_indicators']:
            print(f"[DEBUG] 检查失败: 未选择指标")
            return jsonify({
                'success': False,
                'message': '请先选择指标'
            })
        
        if not app_state['weights']:
            print(f"[DEBUG] 检查失败: 未设置权重")
            return jsonify({
                'success': False,
                'message': '请先设置权重'
            })
        
        if not app_state['ranges']:
            print(f"[DEBUG] 检查失败: 未设置范围，当前ranges: {app_state['ranges']}")
            return jsonify({
                'success': False,
                'message': '请先设置指标范围'
            })
        
        if not app_state['measured_values']:
            print(f"[DEBUG] 检查失败: 未输入实测值")
            return jsonify({
                'success': False,
                'message': '请先输入实测值'
            })
        
        # 计算各指标得分
        indicator_results = []
        total_weighted_score = 0.0
        
        for indicator in app_state['selected_indicators']:
            indicator_id = indicator['id']
            
            if indicator_id not in app_state['measured_values']:
                continue
            
            measured_value = app_state['measured_values'][indicator_id]
            range_data = app_state['ranges'].get(indicator_id, {})
            weight = app_state['weights'].get(indicator_id, 0)
            
            # 使用新的五级评价标准计算得分和等级
            score, grade = calculate_indicator_score_new(measured_value, range_data)
            
            indicator_results.append({
                'indicator_id': indicator_id,
                'indicator_name': indicator['name'],
                'measured_value': measured_value,
                'score': score,
                'grade': grade,
                'weight': weight
            })
            
            total_weighted_score += score * weight
        
        overall_grade = get_grade_from_score(total_weighted_score)
        
        from datetime import datetime
        
        result = {
            'overall_score': total_weighted_score,
            'overall_grade': overall_grade,
            'indicator_results': indicator_results,
            'calculation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"[DEBUG] 计算结果: {result}")
        print(f"[DEBUG] 总加权得分: {total_weighted_score}")
        print(f"[DEBUG] 指标结果数量: {len(indicator_results)}")
        
        app_state['evaluation_result'] = result
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '综合评价计算完成'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'综合评价计算失败: {str(e)}'
        })

@app.route('/api/state')
def get_state():
    """获取应用状态"""
    return jsonify({
        'success': True,
        'data': {
            'selected_indicators_count': len(app_state['selected_indicators']),
            'has_weights': bool(app_state['weights']),
            'has_ranges': bool(app_state['ranges']),
            'has_measured_values': bool(app_state['measured_values']),
            'has_evaluation_result': bool(app_state['evaluation_result'])
        }
    })

@app.route('/api/reset', methods=['POST'])
def reset_state():
    """重置应用状态"""
    global app_state
    app_state = {
        'indicators': app_state['indicators'],  # 保留指标数据
        'selected_indicators': [],
        'weights': {},
        'ranges': {},
        'measured_values': {},
        'evaluation_result': None
    }
    
    return jsonify({
        'success': True,
        'message': '应用状态已重置'
    })

@app.route('/static/components/<path:filename>')
def serve_components(filename):
    """提供组件文件访问"""
    return send_from_directory('templates/components', filename)

@app.route('/test')
def test_page():
    """测试页面"""
    return render_template('test.html')

if __name__ == '__main__':
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='露天台阶爆破效果综合评价系统')
    parser.add_argument('--external', action='store_true', 
                       help='启用外网访问（警告：仅用于演示，生产环境请配置防火墙）')
    parser.add_argument('--ngrok', action='store_true', 
                       help='使用ngrok创建公网隧道')
    parser.add_argument('--ngrok-token', type=str, 
                       help='ngrok认证token')
    parser.add_argument('--port', type=int, default=5000, 
                       help='指定端口号（默认：5000）')
    args = parser.parse_args()
    
    # 创建必要的目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # 加载指标数据
    if not load_indicators():
        print("警告: 无法加载指标数据，请检查 config/indicators.json 文件")
    
    print("露天台阶爆破效果综合评价系统 - 演示版本")
    print("启动Flask服务器...")
    
    # 配置ngrok
    ngrok_tunnel = None
    if args.ngrok and NGROK_AVAILABLE:
        try:
            # 设置authtoken
            if args.ngrok_token:
                ngrok.set_auth_token(args.ngrok_token)
            else:
                # 使用提供的默认token
                ngrok.set_auth_token("31PPEy8orAqByvl8mLu8ekK1dlw_5j9dsMKk1cZvVbGpKocPq")
            
            print("🚀 正在创建ngrok隧道...")
            ngrok_tunnel = ngrok.connect(args.port)
            public_url = ngrok_tunnel.public_url
            print(f"🌐 公网访问地址: {public_url}")
            print(f"🏠 本地访问地址: http://localhost:{args.port}")
            print("⚠️  注意: ngrok隧道将在程序结束时自动关闭")
        except Exception as e:
            print(f"❌ ngrok隧道创建失败: {e}")
            print("将使用本地模式启动...")
    elif args.ngrok and not NGROK_AVAILABLE:
        print("❌ 无法使用ngrok: pyngrok未安装")
        print("请运行: pip install pyngrok")
    
    if args.external:
        print("⚠️  警告: 已启用外网访问模式")
        print("⚠️  请确保在安全的网络环境中使用")
        print(f"🌐 外网访问地址: http://0.0.0.0:{args.port}")
        print(f"🏠 本地访问地址: http://localhost:{args.port}")
        host = '0.0.0.0'
    else:
        print(f"🏠 本地访问地址: http://localhost:{args.port}")
        print("💡 提示: 使用 --external 参数启用外网访问")
        print("💡 提示: 使用 --ngrok 参数创建公网隧道")
        host = '127.0.0.1'
    
    try:
        app.run(host=host, port=args.port, debug=True)
    finally:
        # 清理ngrok隧道
        if ngrok_tunnel:
            print("\n🔄 正在关闭ngrok隧道...")
            ngrok.disconnect(ngrok_tunnel.public_url)
            ngrok.kill()
