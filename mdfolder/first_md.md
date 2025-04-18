# 품질검사 KPI 관리 시스템 가이드

## 목차
1. [시스템 개요](#시스템-개요)
2. [기능 구성](#기능-구성)
3. [데이터 구조](#데이터-구조)
4. [주요 화면](#주요-화면)
5. [시스템 설정](#시스템-설정)

## 시스템 개요

### 목적
- 품질검사 프로세스의 효율적 관리
- 실시간 성과 모니터링
- 데이터 기반 의사결정 지원

### 주요 기능
- 일일 검사 데이터 입력
- 실시간 성과 분석
- 자동화된 보고서 생성
- 알림 시스템

## 기능 구성

### 1. 기본 정보 관리
- 검사원 정보
  - ID
  - 이름
  - 소속 부서
  - 담당 공정
- 공정 정보
  - 공정 코드
  - 공정 명
  - 표준 작업 시간

### 2. 일일 성과 관리
- 검사 데이터 입력
  - 날짜
  - 검사원 ID
  - 담당 공정
  - 검사 수량
  - 불량 수량
  - 작업 시간
- 자동 계산 항목
  - 불량률 = (불량 수량 / 검사 수량) * 100
  - 효율성 = (검사 수량 / 작업 시간) * 100

### 3. 대시보드
- 실시간 모니터링
  - 당일 검사 현황
  - 불량률 추이
  - 검사원별 성과
- 월간 리포트
  - 월간 평균 불량률
  - 최고 성과자
  - 개선 필요 항목

## 데이터 구조

### 검사원 정보 테이블