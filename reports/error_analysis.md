# RebootRoute 오류분석 및 해석 리포트

## 목적
이 리포트는 capstone 발표에서 요구하는 baseline 비교, 모델 성능 해석, confusion matrix, 실패 조건, 한계 설명을 한 파일에서 확인하기 위한 산출물입니다.

## 학습 산출물
- Data version: `03084bbbcc1e8b4f`
- Stage model: `gradient_boosting`
- Mission success model: `logistic_regression`
- Feature columns: 33개

## Baseline 비교

### Stage classifier
| model | accuracy | macro_f1 |
| --- | --- | --- |
| dummy_most_frequent | 0.289 | 0.056 |
| logistic_regression | 0.600 | 0.572 |
| random_forest | 0.689 | 0.526 |
| gradient_boosting | 0.711 | 0.654 |

### Mission success predictor
| model | accuracy | macro_f1 | roc_auc |
| --- | --- | --- | --- |
| dummy_stratified | 0.489 | 0.480 | 0.486 |
| logistic_regression | 0.822 | 0.822 | 0.941 |
| random_forest | 0.889 | 0.889 | 0.931 |
| gradient_boosting | 0.911 | 0.911 | 0.937 |

## Confusion matrix

### Stage classifier
Stage 번호는 API/검증 화면의 내부 단계입니다. 사용자 화면에는 단계 번호를 노출하지 않습니다.

| actual \ predicted | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 11 | 2 | 0 | 0 | 0 | 0 | 0 |
| 2 | 0 | 1 | 9 | 0 | 0 | 0 | 1 | 0 |
| 3 | 0 | 0 | 2 | 3 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 1 |
| 5 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| 6 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 |
| 7 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |

### Mission success predictor
| actual \ predicted | not completed | completed |
| --- | --- | --- |
| not completed | 19 | 3 |
| completed | 5 | 18 |

## 취약 구간
| stage | precision | recall | f1 | support |
| --- | --- | --- | --- | --- |
| 지원 결과/자립 연결 | 0.000 | 0.000 | 0.000 | 2.000 |
| 미니 일경험 | 0.500 | 0.667 | 0.571 | 3.000 |
| 짧은 외출 | 0.600 | 0.600 | 0.600 | 5.000 |

## Mission success reliability summary
| probability bin | mean predicted | observed success | count |
| --- | --- | --- | --- |
| 0.0-0.2 | 0.019 | 0.059 | 17 |
| 0.2-0.4 | 0.340 | 0.400 | 5 |
| 0.4-0.6 | 0.478 | 0.667 | 3 |
| 0.6-0.8 | 0.694 | 1.000 | 2 |
| 0.8-1.0 | 0.960 | 0.889 | 18 |

## 해석 관점
- 추천의 1차 기준은 rule-based stage classifier와 공식 자원 속성입니다.
- ML 모델은 MLOps 시연, 내부 검증, 설명 요인 보조 목적으로 사용합니다.
- 주요 feature는 부담도, 에너지, 생활 리듬, 선호 접촉 방식, 최근 완료/too-hard 로그, 관심 분야입니다.
- 높은 `recent_too_hard_rate`, 높은 외출/대면 부담, 낮은 에너지/생활 리듬은 낮은 부담의 다음 행동으로 보내는 신호입니다.

## 주요 실패 조건
- 현재 stage label과 mission success label은 실제 사용자 관측값이 아니라 synthetic MVP label입니다.
- support가 작은 stage는 macro F1 변동이 큽니다. 특히 상위 단계는 표본이 적어 confusion matrix에서 오분류가 크게 보입니다.
- TF-IDF RAG는 `sample_resources.csv`에 수집된 공식 자원 안에서만 검색합니다. 수집되지 않았거나 DOM 변경으로 빠진 프로그램은 추천하지 못합니다.
- 거리 계산은 수집 자원의 위도/경도 또는 구/군 중심 좌표와 사용자의 데모 위치 입력을 기반으로 한 근사값입니다.
- 안전 표현이 감지되면 일반 추천이 아니라 안전 안내로 분기해야 하며, 이 흐름은 성능 지표가 아니라 정책/안전 요구사항입니다.

## 발표 시 해석 문장
현재 모델 성능은 "운영 성능"이 아니라 "파이프라인이 baseline보다 의미 있는 신호를 학습할 수 있는지"를 보여주는 MVP 검증 결과입니다. 실제 배포 전에는 미션 완료, too-hard 피드백, 프로그램 참여, 지원 결과, 운영자 review를 실제 관측 데이터로 교체하고 같은 리포트를 재생성해야 합니다.

## 필수 고지
현재 학습 label은 사용자 행동과 기관 결과를 대신한 synthetic placeholder입니다. 로그 수집, 운영자 검토, 재학습 구조는 구현되어 있지만, 실제 미션 완료, too-hard 피드백, 프로그램 참여, 지원 결과처럼 관측이 필요한 outcome label은 운영 또는 기관 연계 후 수집·import해야 합니다.
