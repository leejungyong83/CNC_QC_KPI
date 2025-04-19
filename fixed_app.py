def save_inspection_data(data):
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
        
        print(f"저장할 데이터: {english_data}")  # 디버깅용 로그 추가
        
        # 영문 필드명으로 저장
        try:
            response = supabase.table('inspection_data').insert(english_data).execute()
            print(f"Supabase 저장 성공")
            return response
        except Exception as db_error:
            print(f"Supabase 저장 오류: {str(db_error)}")
            # 데이터베이스 연결 실패 시 로컬에 저장
            if 'saved_inspections' not in st.session_state:
                st.session_state.saved_inspections = []
            st.session_state.saved_inspections.append(data)
            raise db_error
            
    except Exception as e:
        print(f"검사 데이터 저장 중 오류: {str(e)}")
        # 세션에 데이터 저장(백업)
        if 'saved_inspections' not in st.session_state:
            st.session_state.saved_inspections = []
        st.session_state.saved_inspections.append(data)
        raise e 