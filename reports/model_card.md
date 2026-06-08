# RebootRoute 모델 카드

## 모델
- Stage classifier: `gradient_boosting`
- Mission success predictor: `logistic_regression`

## 학습 데이터
- Data version: `03084bbbcc1e8b4f`
- 학습 시각: `2026-06-08T10:39:02.108539+00:00`

## 지표
- Stage macro F1: `0.6538690476190476`
- Stage accuracy: `0.7111111111111111`
- Mission success macro F1: `0.8221343873517787`
- Mission success ROC-AUC: `0.9407114624505929`

## 안전성과 해석 가능성
추천의 1차 기준은 rule-based stage classifier입니다. ML 모델은 MLOps 시연과 보조 설명 요인 제공을 위해 포함합니다.

## Label 상태
현재 label은 MVP 시연을 위한 synthetic label입니다. 운영 환경에서는 실제 프로그램 참여, 미션 완료, too-hard 피드백, 상담 준비도, 지원 결과 데이터로 반드시 교체해야 합니다.

필수 원문 고지:
These labels are synthetic MVP labels and must be replaced with real program participation / mission completion / support outcome data before production use.

## 운영 배포 준비도
현재는 운영 배포용이 아닙니다. 실제 배포 전에는 label 교체, 구/군 및 접근성 조건별 편향 점검, 운영자 검증, 지역 기관 연계 프로토콜 수립이 필요합니다.
