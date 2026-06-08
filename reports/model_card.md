# RebootRoute 모델 카드

## 모델
- Stage classifier: `gradient_boosting`
- Mission success predictor: `logistic_regression`

## 학습 데이터
- Data version: `03084bbbcc1e8b4f`
- 학습 시각: `2026-06-08T11:46:24.382693+00:00`

## 지표
- Stage macro F1: `0.6538690476190476`
- Stage accuracy: `0.7111111111111111`
- Mission success macro F1: `0.8221343873517787`
- Mission success ROC-AUC: `0.9407114624505929`

## 안전성과 해석 가능성
추천의 1차 기준은 rule-based stage classifier입니다. ML 모델은 MLOps 시연과 보조 설명 요인 제공을 위해 포함합니다.

## Label 상태
현재 학습 label은 사용자 행동과 기관 결과를 대신한 synthetic placeholder입니다. 로그 수집, 운영자 검토, 재학습 구조는 구현되어 있지만, 실제 미션 완료, too-hard 피드백, 프로그램 참여, 지원 결과처럼 관측이 필요한 outcome label은 운영 또는 기관 연계 후 수집·import해야 합니다.

필수 원문 고지:
The current training labels are synthetic placeholders for user behavior and institution outcome labels. The logging, review, and retraining pipeline is implemented, but real observed mission completion, too-hard feedback, program participation, and support outcome labels must be collected or imported before production use.

## 운영 배포 준비도
현재는 운영 배포용이 아닙니다. 실제 배포 전에는 사용자 행동·기관 outcome label 수집/연계, 구/군 및 접근성 조건별 편향 점검, 운영자 검증, 지역 기관 연계 프로토콜 수립이 필요합니다.
