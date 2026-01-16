"""
MSDS（化学品安全技术说明书）数据管理模块
用于管理化学品的危险性和安全信息
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
import re


class HazardClass(Enum):
    """危险类别"""
    FLAMMABLE = "易燃"
    EXPLOSIVE = "爆炸品"
    OXIDIZING = "氧化性"
    TOXIC = "有毒"
    CORROSIVE = "腐蚀性"
    IRRITANT = "刺激性"
    HEALTH_HAZARD = "健康危害"
    ENVIRONMENTAL_HAZARD = "环境危害"


class GHSHazardCode:
    """GHS危险代码"""
    # 物理危害
    H200 = "爆炸物，不稳定爆炸物"
    H201 = "爆炸物，1.1项"
    H202 = "爆炸物，1.2项"
    H203 = "爆炸物，1.3项"
    H204 = "爆炸物，1.4项"
    H205 = "爆炸物，1.5项"
    H220 = "极易燃气体"
    H221 = "易燃气体"
    H222 = "极易燃喷雾剂"
    H223 = "易燃喷雾剂"
    H224 = "极易燃液体和蒸气"
    H225 = "高度易燃液体和蒸气"
    H226 = "易燃液体和蒸气"
    # 健康危害
    H300 = "吞咽致命"
    H301 = "吞咽有毒"
    H302 = "吞咽有害"
    H310 = "皮肤接触致命"
    H311 = "皮肤接触有毒"
    H312 = "皮肤接触有害"
    H314 = "造成严重皮肤灼伤和眼损伤"
    H315 = "引起皮肤刺激"
    H317 = "可能导致皮肤过敏反应"
    H318 = "造成严重眼损伤"
    H319 = "造成严重眼刺激"
    H330 = "吸入致命"
    H331 = "吸入有毒"
    H332 = "吸入有害"
    H334 = "吸入可能导致过敏或哮喘症状或呼吸困难"
    H335 = "可能引起呼吸道刺激"
    H336 = "可能引起昏昏欲睡或眩晕"
    H340 = "可能导致遗传性缺陷"
    H341 = "怀疑会导致遗传性缺陷"
    H350 = "可能致癌"
    H351 = "怀疑会致癌"
    H360 = "可能对生育能力或胎儿造成伤害"
    H361 = "怀疑对生育能力或胎儿造成伤害"
    H362 = "可能对母乳喂养的儿童造成伤害"
    H370 = "对器官造成损害"
    H371 = "可能对器官造成损害"
    H372 = "长期或重复接触会对器官造成损害"
    H373 = "长期或重复接触可能对器官造成损害"
    # 环境危害
    H400 = "对水生生物毒性非常大"
    H410 = "对水生生物毒性非常大并具有长期持续影响"
    H411 = "对水生生物有毒并具有长期持续影响"
    H412 = "对水生生物有害并具有长期持续影响"
    H413 = "可能对水生生物造成长期持续的有害影响"


@dataclass
class FirstAidMeasure:
    """急救措施"""
    inhalation: str = ""
    skin_contact: str = ""
    eye_contact: str = ""
    ingestion: str = ""


@dataclass
class FireFightingMeasure:
    """消防措施"""
    suitable_extinguishing_media: str = ""
    specific_hazards: str = ""
    protective_equipment: str = ""


@dataclass
class ExposureControl:
    """接触控制/个体防护"""
    engineering_controls: str = ""
    personal_protective_equipment: str = ""
    hygiene_measures: str = ""


class MSDSManager:
    """MSDS数据管理器"""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.msds_records = {}
        
    def create_msds(self, chemical_data: Dict) -> str:
        """创建MSDS记录"""
        required_fields = ['chemical_name', 'cas_number', 'manufacturer']
        for field in required_fields:
            if field not in chemical_data:
                raise ValueError(f"缺少必填字段: {field}")
        
        msds_id = f"MSDS{datetime.now().strftime('%Y%m%d%H%M%S')}"
        chemical_data['msds_id'] = msds_id
        chemical_data['created_date'] = datetime.now()
        chemical_data['revision_date'] = datetime.now()
        chemical_data['version'] = 1.0
        
        # 验证CAS号格式
        if not self._validate_cas_number(chemical_data['cas_number']):
            raise ValueError("无效的CAS号格式")
        
        if self.db:
            success = self.db.insert('msds', chemical_data)
            if success:
                self.msds_records[msds_id] = chemical_data
                return msds_id
        else:
            self.msds_records[msds_id] = chemical_data
            return msds_id
        
        return None
    
    def _validate_cas_number(self, cas_number: str) -> bool:
        """验证CAS号格式"""
        pattern = r'^\d{1,7}-\d{2}-\d$'
        if not re.match(pattern, cas_number):
            return False
        
        # 计算校验码
        parts = cas_number.split('-')
        digits = parts[0] + parts[1]
        check_digit = int(parts[2])
        
        # 计算加权和
        total = 0
        for i, digit in enumerate(reversed(digits)):
            total += int(digit) * (i + 1)
        
        return total % 10 == check_digit
    
    def get_msds(self, msds_id: str) -> Optional[Dict]:
        """获取MSDS信息"""
        if self.db:
            return self.db.query_one('msds', {'msds_id': msds_id})
        return self.msds_records.get(msds_id)
    
    def update_msds(self, msds_id: str, updates: Dict) -> bool:
        """更新MSDS信息"""
        current = self.get_msds(msds_id)
        if not current:
            return False
        
        # 增加版本号
        current_version = current.get('version', 1.0)
        updates['version'] = current_version + 0.1
        updates['revision_date'] = datetime.now()
        
        if self.db:
            return self.db.update('msds', {'msds_id': msds_id}, updates)
        elif msds_id in self.msds_records:
            self.msds_records[msds_id].update(updates)
            return True
        
        return False
    
    def search_msds(self, keyword: str = None, 
                   hazard_class: HazardClass = None,
                   manufacturer: str = None) -> List[Dict]:
        """搜索MSDS记录"""
        results = []
        
        if self.db:
            query = {}
            if keyword:
                query['chemical_name'] = f'%{keyword}%'
            if hazard_class:
                query['hazard_classes'] = f'%{hazard_class.value}%'
            if manufacturer:
                query['manufacturer'] = manufacturer
            results = self.db.query('msds', query)
        else:
            for msds in self.msds_records.values():
                match = True
                if keyword and keyword.lower() not in msds.get('chemical_name', '').lower():
                    match = False
                if hazard_class and hazard_class.value not in msds.get('hazard_classes', []):
                    match = False
                if manufacturer and msds.get('manufacturer', '').lower() != manufacturer.lower():
                    match = False
                if match:
                    results.append(msds)
        
        return results
    
    def calculate_hazard_rating(self, msds_data: Dict) -> Dict:
        """计算危险等级评分"""
        hazard_classes = msds_data.get('hazard_classes', [])
        ghs_codes = msds_data.get('ghs_codes', [])
        
        rating = {
            'flammability': 0,
            'toxicity': 0,
            'reactivity': 0,
            'environmental': 0,
            'overall': 0
        }
        
        # 分析GHS代码确定危险等级
        for code in ghs_codes:
            if code.startswith('H22'):  # 易燃相关
                rating['flammability'] = max(rating['flammability'], 3)
            elif code in ['H224', 'H225']:
                rating['flammability'] = max(rating['flammability'], 4)
            elif code in ['H300', 'H310', 'H330']:  # 致命毒性
                rating['toxicity'] = max(rating['toxicity'], 4)
            elif code.startswith('H30') or code.startswith('H31') or code.startswith('H33'):
                rating['toxicity'] = max(rating['toxicity'], 3)
            elif code.startswith('H20'):  # 爆炸性
                rating['reactivity'] = max(rating['reactivity'], 4)
            elif code.startswith('H40'):  # 环境危害
                rating['environmental'] = max(rating['environmental'], 3)
        
        # 计算总体危险等级
        rating['overall'] = max(rating.values())
        
        return rating
    
    def generate_safety_summary(self, msds_id: str) -> str:
        """生成安全摘要"""
        msds = self.get_msds(msds_id)
        if not msds:
            return ""
        
        summary = f"""
        ===========================================
        化学品安全技术说明书 (MSDS) 摘要
        ===========================================
        化学品名称: {msds.get('chemical_name', 'N/A')}
        CAS号: {msds.get('cas_number', 'N/A')}
        制造商: {msds.get('manufacturer', 'N/A')}
        
        === 危险性概述 ===
        危险类别: {', '.join(msds.get('hazard_classes', []))}
        GHS危险说明: {', '.join(msds.get('ghs_codes', []))}
        
        === 急救措施 ===
        吸入: {msds.get('first_aid', {}).get('inhalation', 'N/A')}
        皮肤接触: {msds.get('first_aid', {}).get('skin_contact', 'N/A')}
        眼睛接触: {msds.get('first_aid', {}).get('eye_contact', 'N/A')}
        食入: {msds.get('first_aid', {}).get('ingestion', 'N/A')}
        
        === 消防措施 ===
        灭火介质: {msds.get('fire_fighting', {}).get('suitable_extinguishing_media', 'N/A')}
        
        === 泄露应急处理 ===
        {msds.get('spill_procedures', 'N/A')}
        
        === 操作处置与储存 ===
        {msds.get('handling_storage', 'N/A')}
        
        === 接触控制/个体防护 ===
        工程控制: {msds.get('exposure_control', {}).get('engineering_controls', 'N/A')}
        个体防护装备: {msds.get('exposure_control', {}).get('personal_protective_equipment', 'N/A')}
        
        === 理化特性 ===
        外观与性状: {msds.get('appearance', 'N/A')}
        熔点: {msds.get('melting_point', 'N/A')}
        沸点: {msds.get('boiling_point', 'N/A')}
        闪点: {msds.get('flash_point', 'N/A')}
        
        === 稳定性和反应性 ===
        {msds.get('stability_reactivity', 'N/A')}
        
        === 生态学资料 ===
        {msds.get('ecological_info', 'N/A')}
        
        === 废弃处置 ===
        {msds.get('disposal_considerations', 'N/A')}
        
        === 法规信息 ===
        {msds.get('regulatory_info', 'N/A')}
        
        === 其他信息 ===
        版本: {msds.get('version', 'N/A')}
        修订日期: {msds.get('revision_date', 'N/A')}
        ===========================================
        """
        
        return summary
    
    def check_compatibility(self, chemical1_id: str, chemical2_id: str) -> Dict:
        """检查化学品兼容性"""
        chem1 = self.get_msds(chemical1_id)
        chem2 = self.get_msds(chemical2_id)
        
        if not chem1 or not chem2:
            return {"error": "化学品不存在"}
        
        compatibility = {
            'compatible': True,
            'warnings': [],
            'incompatibilities': [],
            'reaction_products': []
        }
        
        # 检查已知的不兼容组合
        incompatibles = chem1.get('incompatible_materials', [])
        if chem2.get('chemical_name') in incompatibles:
            compatibility['compatible'] = False
            compatibility['incompatibilities'].append(
                f"{chem1['chemical_name']} 与 {chem2['chemical_name']} 不相容"
            )
        
        # 检查反应性
        reactivity1 = chem1.get('reactivity', {})
        reactivity2 = chem2.get('reactivity', {})
        
        # 检查酸碱反应
        if (reactivity1.get('ph') < 7 and reactivity2.get('ph') > 7) or \
           (reactivity1.get('ph') > 7 and reactivity2.get('ph') < 7):
            compatibility['warnings'].append("酸碱反应可能发生")
        
        # 检查氧化还原反应
        if reactivity1.get('oxidizing_power', 0) > 0 and reactivity2.get('reducing_power', 0) > 0:
            compatibility['warnings'].append("可能发生氧化还原反应")
        
        return compatibility