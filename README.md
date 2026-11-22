# 퇴직연금 영업노트 설정 (무료)

순서를 지켜 주세요.
1. GitHub에서 공개(Public) 저장소를 만듭니다. (README 등 체크 항목은 모두 비움)
2. 공공데이터포털(data.go.kr)에서 "조달청_나라장터 입찰공고정보서비스"를 활용신청해 인증키를 받습니다.
3. 저장소 Settings > Secrets and variables > Actions > New repository secret에 이름 `DATA_GO_KR_KEY`, 값은 인증키로 등록합니다.
4. 저장소에 이 폴더의 파일 4개(`index.html`, `fetch_data.py`, `data.json`, `README.md`)를 올립니다. (uploading an existing file)
5. Settings > Pages에서 Branch를 `main` / `(root)`로 지정하고 Save합니다.
6. 저장소 Code 탭에서 + > Create new file을 누르고, 파일 이름에 `.github/workflows/update.yml`을 입력합니다. `workflow-update.yml`의 내용을 전부 붙여넣고 Commit하면 첫 수집이 바로 실행됩니다.
7. Actions 탭에서 update-data가 초록 체크가 되면 완료입니다. 이후 매일 08:00, 13:00(한국시간)에 자동 갱신됩니다. 수동 실행은 update-data > Run workflow.

주의: 나라장터 API 주소(`fetch_data.py`의 BID_URL)와 응답 항목명은 인증키 발급 후 실제 호출로 확인해야 합니다.
