#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告生成器

负责生成爆破效果评价报告，支持多种格式输出。
包括文本报告、HTML报告、PDF报告等。

作者: 开发团队
版本: 1.0.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from models.evaluation import EvaluationResult, IndicatorResult, CategoryResult
from models.indicators import Indicator, IndicatorCategory
from utils.logger import LoggerMixin


@dataclass
class ReportConfig:
    """
    报告配置
    
    Attributes:
        title: 报告标题
        subtitle: 报告副标题
        author: 报告作者
        organization: 组织机构
        project_name: 项目名称
        project_location: 项目地点
        evaluation_date: 评价日期
        include_charts: 是否包含图表
        include_recommendations: 是否包含建议
        language: 报告语言
    """
    title: str = "露天台阶爆破效果综合评价报告"
    subtitle: str = "Open-pit Bench Blasting Effect Comprehensive Evaluation Report"
    author: str = "评价系统"
    organization: str = "爆破工程评价中心"
    project_name: str = "未命名项目"
    project_location: str = "未指定地点"
    evaluation_date: Optional[datetime] = None
    include_charts: bool = True
    include_recommendations: bool = True
    language: str = "zh-CN"


class ReportGenerator(LoggerMixin):
    """
    报告生成器
    
    负责根据评价结果生成各种格式的报告。
    支持文本、HTML、JSON等格式。
    
    Attributes:
        config: 报告配置
        template_dir: 模板目录
    """
    
    def __init__(self, config: Optional[ReportConfig] = None):
        """
        初始化报告生成器
        
        Args:
            config: 报告配置
        """
        self.config = config or ReportConfig()
        if self.config.evaluation_date is None:
            self.config.evaluation_date = datetime.now()
        
        self.template_dir = Path("templates")
        self.logger.info("报告生成器初始化完成")
    
    def generate_text_report(
        self,
        evaluation_result: EvaluationResult,
        indicators: List[Indicator],
        categories: List[IndicatorCategory],
        output_file: Optional[str] = None
    ) -> str:
        """
        生成文本格式报告
        
        Args:
            evaluation_result: 评价结果
            indicators: 指标列表
            categories: 分类列表
            output_file: 输出文件路径
            
        Returns:
            str: 报告内容
        """
        try:
            # 构建报告内容
            report_lines = []
            
            # 报告头部
            report_lines.extend(self._build_text_header())
            
            # 评价概要
            report_lines.extend(self._build_text_summary(evaluation_result))
            
            # 指标详情
            report_lines.extend(self._build_text_indicator_details(
                evaluation_result, indicators, categories
            ))
            
            # 分类结果
            report_lines.extend(self._build_text_category_results(evaluation_result))
            
            # 改进建议
            if self.config.include_recommendations:
                report_lines.extend(self._build_text_recommendations(evaluation_result))
            
            # 报告尾部
            report_lines.extend(self._build_text_footer())
            
            # 合并内容
            report_content = "\n".join(report_lines)
            
            # 保存到文件
            if output_file:
                self._save_to_file(report_content, output_file)
            
            self.logger.info("文本报告生成完成")
            return report_content
            
        except Exception as e:
            self.logger.error(f"文本报告生成失败: {e}")
            raise
    
    def generate_html_report(
        self,
        evaluation_result: EvaluationResult,
        indicators: List[Indicator],
        categories: List[IndicatorCategory],
        output_file: Optional[str] = None
    ) -> str:
        """
        生成HTML格式报告
        
        Args:
            evaluation_result: 评价结果
            indicators: 指标列表
            categories: 分类列表
            output_file: 输出文件路径
            
        Returns:
            str: HTML报告内容
        """
        try:
            # 构建HTML内容
            html_parts = []
            
            # HTML头部
            html_parts.append(self._build_html_header())
            
            # 报告标题
            html_parts.append(self._build_html_title())
            
            # 评价概要
            html_parts.append(self._build_html_summary(evaluation_result))
            
            # 指标详情表格
            html_parts.append(self._build_html_indicator_table(
                evaluation_result, indicators, categories
            ))
            
            # 分类结果图表
            if self.config.include_charts:
                html_parts.append(self._build_html_category_chart(evaluation_result))
            
            # 改进建议
            if self.config.include_recommendations:
                html_parts.append(self._build_html_recommendations(evaluation_result))
            
            # HTML尾部
            html_parts.append(self._build_html_footer())
            
            # 合并内容
            html_content = "\n".join(html_parts)
            
            # 保存到文件
            if output_file:
                self._save_to_file(html_content, output_file)
            
            self.logger.info("HTML报告生成完成")
            return html_content
            
        except Exception as e:
            self.logger.error(f"HTML报告生成失败: {e}")
            raise
    
    def generate_json_report(
        self,
        evaluation_result: EvaluationResult,
        indicators: List[Indicator],
        categories: List[IndicatorCategory],
        output_file: Optional[str] = None
    ) -> str:
        """
        生成JSON格式报告
        
        Args:
            evaluation_result: 评价结果
            indicators: 指标列表
            categories: 分类列表
            output_file: 输出文件路径
            
        Returns:
            str: JSON报告内容
        """
        try:
            # 构建JSON数据
            report_data = {
                "report_info": {
                    "title": self.config.title,
                    "subtitle": self.config.subtitle,
                    "author": self.config.author,
                    "organization": self.config.organization,
                    "project_name": self.config.project_name,
                    "project_location": self.config.project_location,
                    "evaluation_date": self.config.evaluation_date.isoformat(),
                    "generation_time": datetime.now().isoformat()
                },
                "evaluation_summary": {
                    "total_score": evaluation_result.total_score,
                    "final_grade": evaluation_result.final_grade.value,
                    "grade_description": self._get_grade_description(evaluation_result.final_grade),
                    "evaluation_summary": evaluation_result.summary
                },
                "indicator_results": [
                    {
                        "indicator_id": result.indicator_id,
                        "indicator_name": self._get_indicator_name(result.indicator_id, indicators),
                        "measured_value": result.measured_value,
                        "normalized_value": result.normalized_value,
                        "score": result.score,
                        "grade": result.grade.value,
                        "weight": result.weight
                    }
                    for result in evaluation_result.indicator_results
                ],
                "category_results": [
                    {
                        "category_id": result.category_id,
                        "category_name": self._get_category_name(result.category_id, categories),
                        "score": result.score,
                        "grade": result.grade.value,
                        "weight": result.weight,
                        "indicator_count": len(result.indicator_results)
                    }
                    for result in evaluation_result.category_results
                ],
                "metadata": {
                    "total_indicators": len(evaluation_result.indicator_results),
                    "total_categories": len(evaluation_result.category_results),
                    "weight_method": evaluation_result.weight_method.value if evaluation_result.weight_method else "Unknown"
                }
            }
            
            # 添加改进建议
            if self.config.include_recommendations:
                report_data["recommendations"] = self._generate_recommendations(evaluation_result)
            
            # 转换为JSON字符串
            json_content = json.dumps(report_data, ensure_ascii=False, indent=2)
            
            # 保存到文件
            if output_file:
                self._save_to_file(json_content, output_file)
            
            self.logger.info("JSON报告生成完成")
            return json_content
            
        except Exception as e:
            self.logger.error(f"JSON报告生成失败: {e}")
            raise
    
    def _build_text_header(self) -> List[str]:
        """
        构建文本报告头部
        
        Returns:
            List[str]: 头部内容行
        """
        lines = [
            "=" * 80,
            f"{self.config.title:^80}",
            f"{self.config.subtitle:^80}",
            "=" * 80,
            "",
            f"项目名称: {self.config.project_name}",
            f"项目地点: {self.config.project_location}",
            f"评价日期: {self.config.evaluation_date.strftime('%Y年%m月%d日')}",
            f"报告作者: {self.config.author}",
            f"评价机构: {self.config.organization}",
            f"生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "",
            "-" * 80,
            ""
        ]
        return lines
    
    def _build_text_summary(self, evaluation_result: EvaluationResult) -> List[str]:
        """
        构建文本评价概要
        
        Args:
            evaluation_result: 评价结果
            
        Returns:
            List[str]: 概要内容行
        """
        lines = [
            "一、评价概要",
            "",
            f"综合得分: {evaluation_result.total_score:.2f}分",
            f"评价等级: {evaluation_result.final_grade.value}",
            f"等级描述: {self._get_grade_description(evaluation_result.final_grade)}",
            "",
            "评价总结:",
            evaluation_result.summary,
            "",
            "-" * 80,
            ""
        ]
        return lines
    
    def _build_text_indicator_details(
        self,
        evaluation_result: EvaluationResult,
        indicators: List[Indicator],
        categories: List[IndicatorCategory]
    ) -> List[str]:
        """
        构建文本指标详情
        
        Args:
            evaluation_result: 评价结果
            indicators: 指标列表
            categories: 分类列表
            
        Returns:
            List[str]: 指标详情内容行
        """
        lines = [
            "二、指标评价详情",
            "",
            f"{'指标名称':<20} {'实测值':<12} {'标准化值':<12} {'得分':<8} {'等级':<8} {'权重':<8}",
            "-" * 80
        ]
        
        # 按分类组织指标
        category_indicators = {}
        for result in evaluation_result.indicator_results:
            indicator = self._get_indicator_by_id(result.indicator_id, indicators)
            if indicator:
                category_id = indicator.category_id
                if category_id not in category_indicators:
                    category_indicators[category_id] = []
                category_indicators[category_id].append((indicator, result))
        
        # 输出各分类的指标
        for category in categories:
            if category.id in category_indicators:
                lines.append(f"\n{category.name}:")
                
                for indicator, result in category_indicators[category.id]:
                    lines.append(
                        f"{indicator.name:<20} "
                        f"{result.measured_value:<12.2f} "
                        f"{result.normalized_value:<12.2f} "
                        f"{result.score:<8.2f} "
                        f"{result.grade.value:<8} "
                        f"{result.weight:<8.3f}"
                    )
        
        lines.extend(["", "-" * 80, ""])
        return lines
    
    def _build_text_category_results(self, evaluation_result: EvaluationResult) -> List[str]:
        """
        构建文本分类结果
        
        Args:
            evaluation_result: 评价结果
            
        Returns:
            List[str]: 分类结果内容行
        """
        lines = [
            "三、分类评价结果",
            "",
            f"{'分类名称':<20} {'得分':<10} {'等级':<10} {'权重':<10}",
            "-" * 60
        ]
        
        for result in evaluation_result.category_results:
            category_name = result.category_id  # 简化处理，实际应该获取分类名称
            lines.append(
                f"{category_name:<20} "
                f"{result.score:<10.2f} "
                f"{result.grade.value:<10} "
                f"{result.weight:<10.3f}"
            )
        
        lines.extend(["", "-" * 80, ""])
        return lines
    
    def _build_text_recommendations(self, evaluation_result: EvaluationResult) -> List[str]:
        """
        构建文本改进建议
        
        Args:
            evaluation_result: 评价结果
            
        Returns:
            List[str]: 改进建议内容行
        """
        lines = [
            "四、改进建议",
            ""
        ]
        
        recommendations = self._generate_recommendations(evaluation_result)
        
        for i, recommendation in enumerate(recommendations, 1):
            lines.append(f"{i}. {recommendation}")
        
        lines.extend(["", "-" * 80, ""])
        return lines
    
    def _build_text_footer(self) -> List[str]:
        """
        构建文本报告尾部
        
        Returns:
            List[str]: 尾部内容行
        """
        lines = [
            "报告说明:",
            "1. 本报告基于露天台阶爆破效果综合评价系统生成",
            "2. 评价结果仅供参考，具体应用需结合实际情况",
            "3. 如有疑问，请联系评价机构进行咨询",
            "",
            "=" * 80,
            f"报告结束 - {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            "=" * 80
        ]
        return lines
    
    def _build_html_header(self) -> str:
        """
        构建HTML头部
        
        Returns:
            str: HTML头部内容
        """
        return f"""
<!DOCTYPE html>
<html lang="{self.config.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.title}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-size: 16px;
            color: #666;
            margin-bottom: 20px;
        }}
        .info-table {{
            width: 100%;
            margin-bottom: 20px;
        }}
        .info-table td {{
            padding: 5px 10px;
            border-bottom: 1px solid #eee;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: bold;
            color: #007bff;
            border-left: 4px solid #007bff;
            padding-left: 10px;
            margin-bottom: 15px;
        }}
        .summary-box {{
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .score-display {{
            font-size: 24px;
            font-weight: bold;
            color: #28a745;
            text-align: center;
            margin: 10px 0;
        }}
        .grade-display {{
            font-size: 18px;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .grade-excellent {{ background-color: #d4edda; color: #155724; }}
        .grade-good {{ background-color: #d1ecf1; color: #0c5460; }}
        .grade-average {{ background-color: #fff3cd; color: #856404; }}
        .grade-poor {{ background-color: #f8d7da; color: #721c24; }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .data-table th, .data-table td {{
            border: 1px solid #dee2e6;
            padding: 8px 12px;
            text-align: left;
        }}
        .data-table th {{
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }}
        .data-table tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .recommendations {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
        }}
        .recommendations ul {{
            margin: 0;
            padding-left: 20px;
        }}
        .footer {{
            border-top: 1px solid #dee2e6;
            padding-top: 20px;
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
"""
    
    def _build_html_title(self) -> str:
        """
        构建HTML标题
        
        Returns:
            str: HTML标题内容
        """
        return f"""
        <div class="header">
            <div class="title">{self.config.title}</div>
            <div class="subtitle">{self.config.subtitle}</div>
            <table class="info-table">
                <tr>
                    <td><strong>项目名称:</strong></td>
                    <td>{self.config.project_name}</td>
                    <td><strong>项目地点:</strong></td>
                    <td>{self.config.project_location}</td>
                </tr>
                <tr>
                    <td><strong>评价日期:</strong></td>
                    <td>{self.config.evaluation_date.strftime('%Y年%m月%d日')}</td>
                    <td><strong>报告作者:</strong></td>
                    <td>{self.config.author}</td>
                </tr>
                <tr>
                    <td><strong>评价机构:</strong></td>
                    <td>{self.config.organization}</td>
                    <td><strong>生成时间:</strong></td>
                    <td>{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</td>
                </tr>
            </table>
        </div>
"""
    
    def _build_html_summary(self, evaluation_result: EvaluationResult) -> str:
        """
        构建HTML评价概要
        
        Args:
            evaluation_result: 评价结果
            
        Returns:
            str: HTML概要内容
        """
        grade_class = f"grade-{evaluation_result.final_grade.value.lower()}"
        
        return f"""
        <div class="section">
            <div class="section-title">一、评价概要</div>
            <div class="summary-box">
                <div class="score-display">综合得分: {evaluation_result.total_score:.2f}分</div>
                <div class="grade-display {grade_class}">
                    评价等级: {evaluation_result.final_grade.value} - {self._get_grade_description(evaluation_result.final_grade)}
                </div>
                <div style="margin-top: 15px;">
                    <strong>评价总结:</strong><br>
                    {evaluation_result.summary}
                </div>
            </div>
        </div>
"""
    
    def _build_html_indicator_table(
        self,
        evaluation_result: EvaluationResult,
        indicators: List[Indicator],
        categories: List[IndicatorCategory]
    ) -> str:
        """
        构建HTML指标详情表格
        
        Args:
            evaluation_result: 评价结果
            indicators: 指标列表
            categories: 分类列表
            
        Returns:
            str: HTML表格内容
        """
        table_rows = []
        
        # 按分类组织指标
        category_indicators = {}
        for result in evaluation_result.indicator_results:
            indicator = self._get_indicator_by_id(result.indicator_id, indicators)
            if indicator:
                category_id = indicator.category_id
                if category_id not in category_indicators:
                    category_indicators[category_id] = []
                category_indicators[category_id].append((indicator, result))
        
        # 生成表格行
        for category in categories:
            if category.id in category_indicators:
                # 分类标题行
                table_rows.append(
                    f'<tr style="background-color: #e9ecef;">'
                    f'<td colspan="6"><strong>{category.name}</strong></td></tr>'
                )
                
                # 指标数据行
                for indicator, result in category_indicators[category.id]:
                    grade_class = f"grade-{result.grade.value.lower()}"
                    table_rows.append(
                        f'<tr>'
                        f'<td>{indicator.name}</td>'
                        f'<td>{result.measured_value:.2f} {indicator.unit}</td>'
                        f'<td>{result.normalized_value:.2f}</td>'
                        f'<td>{result.score:.2f}</td>'
                        f'<td><span class="{grade_class}" style="padding: 2px 6px; border-radius: 3px;">{result.grade.value}</span></td>'
                        f'<td>{result.weight:.3f}</td>'
                        f'</tr>'
                    )
        
        return f"""
        <div class="section">
            <div class="section-title">二、指标评价详情</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>指标名称</th>
                        <th>实测值</th>
                        <th>标准化值</th>
                        <th>得分</th>
                        <th>等级</th>
                        <th>权重</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
"""
    
    def _build_html_category_chart(self, evaluation_result: EvaluationResult) -> str:
        """
        构建HTML分类结果图表
        
        Args:
            evaluation_result: 评价结果
            
        Returns:
            str: HTML图表内容
        """
        # 简化处理，生成表格而非图表
        table_rows = []
        
        for result in evaluation_result.category_results:
            grade_class = f"grade-{result.grade.value.lower()}"
            table_rows.append(
                f'<tr>'
                f'<td>{result.category_id}</td>'
                f'<td>{result.score:.2f}</td>'
                f'<td><span class="{grade_class}" style="padding: 2px 6px; border-radius: 3px;">{result.grade.value}</span></td>'
                f'<td>{result.weight:.3f}</td>'
                f'</tr>'
            )
        
        return f"""
        <div class="section">
            <div class="section-title">三、分类评价结果</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>分类名称</th>
                        <th>得分</th>
                        <th>等级</th>
                        <th>权重</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
"""
    
    def _build_html_recommendations(self, evaluation_result: EvaluationResult) -> str:
        """
        构建HTML改进建议
        
        Args:
            evaluation_result: 评价结果
            
        Returns:
            str: HTML改进建议内容
        """
        recommendations = self._generate_recommendations(evaluation_result)
        
        recommendation_items = []
        for recommendation in recommendations:
            recommendation_items.append(f'<li>{recommendation}</li>')
        
        return f"""
        <div class="section">
            <div class="section-title">四、改进建议</div>
            <div class="recommendations">
                <ul>
                    {''.join(recommendation_items)}
                </ul>
            </div>
        </div>
"""
    
    def _build_html_footer(self) -> str:
        """
        构建HTML尾部
        
        Returns:
            str: HTML尾部内容
        """
        return f"""
        <div class="footer">
            <p><strong>报告说明:</strong></p>
            <p>1. 本报告基于露天台阶爆破效果综合评价系统生成</p>
            <p>2. 评价结果仅供参考，具体应用需结合实际情况</p>
            <p>3. 如有疑问，请联系评价机构进行咨询</p>
            <p>报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _generate_recommendations(self, evaluation_result: EvaluationResult) -> List[str]:
        """
        生成改进建议
        
        Args:
            evaluation_result: 评价结果
            
        Returns:
            List[str]: 建议列表
        """
        recommendations = []
        
        # 根据总体得分给出建议
        if evaluation_result.total_score >= 90:
            recommendations.append("爆破效果优秀，继续保持当前的爆破参数和施工工艺")
        elif evaluation_result.total_score >= 80:
            recommendations.append("爆破效果良好，可适当优化部分参数以进一步提升效果")
        elif evaluation_result.total_score >= 70:
            recommendations.append("爆破效果一般，建议重点改进得分较低的指标")
        else:
            recommendations.append("爆破效果较差，需要全面检查和调整爆破设计方案")
        
        # 根据具体指标给出建议
        poor_indicators = [
            result for result in evaluation_result.indicator_results
            if result.score < 70
        ]
        
        if poor_indicators:
            recommendations.append(f"重点关注以下{len(poor_indicators)}个得分较低的指标，制定针对性改进措施")
            
            for result in poor_indicators[:3]:  # 最多显示3个
                if "大块率" in result.indicator_id:
                    recommendations.append("优化炸药分布和起爆顺序，减少大块产生")
                elif "根底" in result.indicator_id:
                    recommendations.append("调整底部装药量和延时时间，改善根底清理效果")
                elif "飞石" in result.indicator_id:
                    recommendations.append("加强覆盖措施，优化装药结构，控制飞石距离")
                elif "振动" in result.indicator_id:
                    recommendations.append("采用微差爆破技术，减少单段装药量，降低爆破振动")
        
        # 根据分类结果给出建议
        poor_categories = [
            result for result in evaluation_result.category_results
            if result.score < 75
        ]
        
        if poor_categories:
            for result in poor_categories:
                if "technical" in result.category_id:
                    recommendations.append("加强爆破质量控制，优化钻孔参数和装药结构")
                elif "safety" in result.category_id:
                    recommendations.append("强化安全防护措施，严格控制爆破安全距离")
                elif "economic" in result.category_id:
                    recommendations.append("优化炸药配比和用量，提高爆破经济效益")
        
        return recommendations
    
    def _get_grade_description(self, grade) -> str:
        """
        获取等级描述
        
        Args:
            grade: 评价等级
            
        Returns:
            str: 等级描述
        """
        descriptions = {
            "优秀": "优秀",
            "良好": "良好",
            "一般": "一般",
            "较差": "较差",
            "很差": "很差",
            "Excellent": "优秀",
            "Good": "良好", 
            "Average": "一般",
            "Poor": "较差"
        }
        return descriptions.get(grade.value, "未知")
    
    def _get_indicator_name(self, indicator_id: str, indicators: List[Indicator]) -> str:
        """
        获取指标名称
        
        Args:
            indicator_id: 指标ID
            indicators: 指标列表
            
        Returns:
            str: 指标名称
        """
        for indicator in indicators:
            if indicator.id == indicator_id:
                return indicator.name
        return indicator_id
    
    def _get_category_name(self, category_id: str, categories: List[IndicatorCategory]) -> str:
        """
        获取分类名称
        
        Args:
            category_id: 分类ID
            categories: 分类列表
            
        Returns:
            str: 分类名称
        """
        for category in categories:
            if category.id == category_id:
                return category.name
        return category_id
    
    def _get_indicator_by_id(self, indicator_id: str, indicators: List[Indicator]) -> Optional[Indicator]:
        """
        根据ID获取指标
        
        Args:
            indicator_id: 指标ID
            indicators: 指标列表
            
        Returns:
            Optional[Indicator]: 指标实例
        """
        for indicator in indicators:
            if indicator.id == indicator_id:
                return indicator
        return None
    
    def _save_to_file(self, content: str, file_path: str) -> None:
        """
        保存内容到文件
        
        Args:
            content: 文件内容
            file_path: 文件路径
        """
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"报告已保存到: {file_path}")
            
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            raise
