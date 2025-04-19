"""
Supabase 연동 문제 해결을 위한 패치 스크립트
- app1.py 파일에서 달성률(%) 필드 관련 코드를 수정합니다.
- save_inspection_data 함수와 load_inspection_data 함수를 수정합니다.
"""

import os
import re

def apply_fix():
    # 백업 파일 생성
    backup_file = "app1_before_fix.py"
    if not os.path.exists(backup_file):
        with open("app1.py", "r", encoding="utf-8") as src:
            content = src.read()
            with open(backup_file, "w", encoding="utf-8") as dst:
                dst.write(content)
                print(f"백업 파일 생성 완료: {backup_file}")
    
    # app1.py 파일 수정
    try:
        with open("app1.py", "r", encoding="utf-8") as file:
            content = file.read()
        
        # 1. save_inspection_data 함수 수정
        save_pattern = r"def save_inspection_data\(data\):.*?(?=# 불량 데이터 저장|def save_defect_data)"
        save_replacement = """def save_inspection_data(data):
    try:
        # 한글 필드명을 영문으로 변환
        field_mapping = {
            "검사원": "inspector_name",
            "공정": "process",
            "모델명": "model_name",
            "검사일자": "inspection_date",
            "검사시간": "inspection_time",
            "LOT번호": "lot_number",
            "작업시간(분)": "work_time_minutes",
            "계획수량": "planned_quantity",
            "검사수량": "total_inspected",
            "불량수량": "total_defects",
            "불량률(%)": "defect_rate",
            # "달성률(%)": "achievement_rate",  # 스키마에 존재하지 않는 컬럼이므로 제거
            "비고": "remarks"
        }
        
        # 데이터 변환
        english_data = {}
        for k, v in data.items():
            if k in field_mapping:
                english_data[field_mapping[k]] = v
            elif k != "달성률(%)":  # 달성률(%) 필드는 무시
                english_data[k] = v
        
        # 불량 세부정보 처리
        if "불량세부" in data:
            defect_details = []
            for item in data["불량세부"]:
                defect_details.append({
                    "type": item["type"],
                    "quantity": item["quantity"]
                })
            english_data["defect_details"] = json.dumps(defect_details, ensure_ascii=False)
        
        # 영문 필드명으로 저장
        try:
            response = supabase.table('inspection_data').insert(english_data).execute()
            return response
        except Exception as db_error:
            # 데이터베이스 연결 실패 시 로컬에 저장
            if 'saved_inspections' not in st.session_state:
                st.session_state.saved_inspections = []
            st.session_state.saved_inspections.append(data)
            raise db_error
            
    except Exception as e:
        # 세션에 데이터 저장(백업)
        if 'saved_inspections' not in st.session_state:
            st.session_state.saved_inspections = []
        st.session_state.saved_inspections.append(data)
        raise e

"""
        
        # 2. load_inspection_data 함수 수정
        load_pattern = r'("achievement_rate": "달성률\(%\)",)'
        load_replacement = '# \\1  # 스키마에 존재하지 않는 컬럼이므로 주석 처리'
        
        # 정규식을 사용하여 패턴 치환 (DOTALL 옵션 사용하여 여러 줄 매칭)
        modified_content = re.sub(save_pattern, save_replacement, content, flags=re.DOTALL)
        modified_content = re.sub(load_pattern, load_replacement, modified_content)
        
        # 수정된 내용을 파일에 저장
        with open("app1_fixed_supabase.py", "w", encoding="utf-8") as file:
            file.write(modified_content)
            print("수정 완료. app1_fixed_supabase.py 파일을 확인하세요.")
            
        print("\n===== 적용 방법 =====")
        print("1. app1_fixed_supabase.py 파일을 app1.py로 교체하거나")
        print("2. 해당 파일을 직접 실행하여 앱을 시작하세요.")
        
        return True
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    apply_fix() 