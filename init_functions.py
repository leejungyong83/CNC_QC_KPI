import pandas as pd
import os
import json
from pathlib import Path
import streamlit as st

# 초기화 함수들
def init_inspection_data():
    """검사 데이터 초기화 함수"""
    try:
        # CSV 파일 확인
        csv_path = "data/inspection_data.csv"
        if os.path.exists(csv_path):
            print(f"CSV 파일 로드: {csv_path}")
            return pd.read_csv(csv_path)
            
        # Supabase에서 직접 데이터 가져오기 시도
        try:
            if 'supabase' in globals() and supabase is not None:
                print("Supabase에서 inspection_data 로드 시도")
                response = supabase.table('inspection_data').select('*').execute()
                if response and hasattr(response, 'data') and response.data:
                    df = pd.DataFrame(response.data)
                    
                    # 영문 필드명을 한글로 변환
                    field_mapping = {
                        "inspector_name": "검사원",
                        "process": "공정",
                        "model_name": "모델명",
                        "inspection_date": "검사일자",
                        "inspection_time": "검사시간",
                        "lot_number": "LOT번호",
                        "work_time_minutes": "작업시간(분)",
                        "planned_quantity": "계획수량",
                        "total_inspected": "검사수량",
                        "total_defects": "불량수량",
                        "defect_rate": "불량률(%)",
                        "achievement_rate": "달성률(%)",
                        "remarks": "비고"
                    }
                    renamed_columns = {}
                    for eng, kor in field_mapping.items():
                        if eng in df.columns:
                            renamed_columns[eng] = kor
                    
                    df = df.rename(columns=renamed_columns)
                    
                    # CSV 파일로 저장 시도
                    try:
                        os.makedirs("data", exist_ok=True)
                        df.to_csv(csv_path, index=False)
                        print(f"Supabase 데이터를 CSV로 저장: {csv_path}")
                    except Exception as save_err:
                        print(f"CSV 저장 실패: {str(save_err)}")
                    
                    return df
        except Exception as db_err:
            print(f"Supabase 데이터 로드 오류: {str(db_err)}")
        
        # 기본 빈 데이터 반환
        print("검사 데이터 초기화: 빈 데이터프레임 생성")
        empty_df = pd.DataFrame(columns=["검사원", "공정", "모델명", "검사일자", "검사시간", "LOT번호"])
        
        # 빈 데이터 저장 시도
        try:
            os.makedirs("data", exist_ok=True)
            empty_df.to_csv(csv_path, index=False)
        except:
            pass
            
        return empty_df
    except Exception as e:
        print(f"검사 데이터 초기화 오류: {str(e)}")
        return pd.DataFrame(columns=["검사원", "공정", "모델명", "검사일자", "검사시간", "LOT번호"])

def init_product_models():
    """생산모델 데이터 초기화 함수"""
    try:
        # CSV 파일 확인
        csv_path = "data/product_models.csv"
        if os.path.exists(csv_path):
            print(f"CSV 파일 로드: {csv_path}")
            return pd.read_csv(csv_path)
        
        # Supabase에서 직접 데이터 가져오기 시도
        try:
            if 'supabase' in globals() and supabase is not None:
                print("Supabase에서 product_models 로드 시도")
                response = supabase.table('product_models').select('*').execute()
                if response and hasattr(response, 'data') and response.data:
                    df = pd.DataFrame(response.data)
                    
                    # CSV 파일로 저장 시도
                    try:
                        os.makedirs("data", exist_ok=True)
                        df.to_csv(csv_path, index=False)
                        print(f"Supabase 모델 데이터를 CSV로 저장: {csv_path}")
                    except Exception as save_err:
                        print(f"CSV 저장 실패: {str(save_err)}")
                    
                    return df
        except Exception as db_err:
            print(f"Supabase 모델 데이터 로드 오류: {str(db_err)}")
        
        # 기본 데이터 생성
        print("생산모델 데이터 초기화: 기본 데이터 생성")
        default_models = [
            {"id": 1, "모델명": "PA1", "공정": "C1"},
            {"id": 2, "모델명": "PA1", "공정": "C2"},
            {"id": 3, "모델명": "PA2", "공정": "C1"},
            {"id": 4, "모델명": "PA2", "공정": "C2"},
            {"id": 5, "모델명": "B6", "공정": "C1"},
            {"id": 6, "모델명": "B6M", "공정": "C1"},
            {"id": 7, "모델명": "B7SUB6", "공정": "C1"},
            {"id": 8, "모델명": "B7SUB6", "공정": "C2"}
        ]
        df = pd.DataFrame(default_models)
        
        # 데이터 디렉토리 확인 및 생성
        os.makedirs("data", exist_ok=True)
        
        # 기본 데이터 저장 시도
        try:
            df.to_csv(csv_path, index=False)
            print(f"기본 모델 데이터 CSV 저장: {csv_path}")
        except Exception as save_err:
            print(f"기본 데이터 저장 실패: {str(save_err)}")
            
        return df
    except Exception as e:
        print(f"생산모델 데이터 초기화 오류: {str(e)}")
        return pd.DataFrame(columns=["id", "모델명", "공정"]) 