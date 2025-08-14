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

def calculate_ahp_weights(matrix: List[List[float]]) -> Optional[List[float]]:
    """计算AHP权重"""
    try:
        matrix = np.array(matrix)
        n = matrix.shape[0]
        
        # 计算特征向量
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_eigenvalue_index = np.argmax(eigenvalues.real)
        principal_eigenvector = eigenvectors[:, max_eigenvalue_index].real
        
        # 归一化权重
        weights = principal_eigenvector / np.sum(principal_eigenvector)
        weights = np.abs(weights)  # 确保权重为正
        
        # 一致性检查
        max_eigenvalue = eigenvalues[max_eigenvalue_index].real
        ci = (max_eigenvalue - n) / (n - 1)
        ri_values = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
        ri = ri_values.get(n, 1.45)
        cr = ci / ri if ri > 0 else 0
        
        if cr > 0.1:
            print(f"警告: 一致性比率 {cr:.3f} > 0.1，判断矩阵一致性较差")
        
        return weights.tolist()
    except Exception as e:
        print(f"AHP权重计算失败: {e}")
        return None

def calculate_indicator_score(value: float, optimal: float, worst: float, is_positive: bool = True) -> float:
    """计算单个指标得分"""
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
        return "优秀"
    elif score >= 80:
        return "良好"
    elif score >= 70:
        return "中等"
    elif score >= 60:
        return "及格"
    else:
        return "不及格"

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
    
    return jsonify({
        'success': True,
        'data': app_state['indicators']
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

@app.route('/api/ranges/set', methods=['POST'])
def set_ranges():
    """设置指标范围"""
    try:
        data = request.get_json()
        ranges = data.get('ranges', {})
        
        app_state['ranges'] = ranges
        
        return jsonify({
            'success': True,
            'message': '指标范围设置完成'
        })
    except Exception as e:
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

@app.route('/api/evaluation/calculate', methods=['POST'])
def calculate_evaluation():
    """执行综合评价"""
    try:
        # 检查数据完整性
        if not app_state['selected_indicators']:
            return jsonify({
                'success': False,
                'message': '请先选择指标'
            })
        
        if not app_state['weights']:
            return jsonify({
                'success': False,
                'message': '请先设置权重'
            })
        
        if not app_state['ranges']:
            return jsonify({
                'success': False,
                'message': '请先设置指标范围'
            })
        
        if not app_state['measured_values']:
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
            
            optimal = range_data.get('optimal', 100)
            worst = range_data.get('worst', 0)
            is_positive = indicator.get('is_positive', True)
            
            score = calculate_indicator_score(measured_value, optimal, worst, is_positive)
            grade = get_grade_from_score(score)
            
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
        
        result = {
            'overall_score': total_weighted_score,
            'overall_grade': overall_grade,
            'indicator_results': indicator_results,
            'calculation_time': '2024-01-XX 12:00:00'
        }
        
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

if __name__ == '__main__':
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
    print("访问地址: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)