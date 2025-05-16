# 1.2.1使用sourcetree

2024年1月23日
下午 03:04

第一次使用sourcetree連線ADO,會需要做事前設定(確認sslVerify):

事前設定(確認sslVerify)

Step1:開啟CMD/bash視窗,用指令確認sslVerify設定

git config -- global http.sslVerify

Step2:如顯示為空,需自行輸入指令設定新增(比照現行bitbucket設定)

git config -- global http.sslVerify false

事前確認完成後,在此步驟會跳出帳號密碼驗證,即可順利使用

![test_page_7_g2.jpg](https://doc-ai-test-sam.s3.ap-southeast-1.amazonaws.com/im
ages/test_page_7_g2.jpg)

<!-- PageFooter="開發作業必備指南 for info 第7頁" -->
