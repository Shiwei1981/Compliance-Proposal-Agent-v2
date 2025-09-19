$OutputEncoding = [System.Text.Encoding]::UTF8  # 设置输出编码  
while ($true) {  
    $userInput = Read-Host "请输入您的输入 (输入 'exit' 退出)"  
  
    if ($userInput -eq 'exit') {  
        break  # 如果用户输入 'exit'，则退出循环  
    }  
  
    # URL 编码用户输入  
    $question = [System.Web.HttpUtility]::UrlEncode($userInput)  
  
    try {  
        # 构建 POST 请求的 URL  
        $url = "http://127.0.0.1:8000/quickquery"  
  
        # 构建请求的主体  
        $body = @{ question = $question }  
  
        # 发送 POST 请求  
        $response = Invoke-WebRequest -Uri $url -Method Post -Body $body  
  
        # 输出原始响应内容  
        $rawContent = $response.RawContent  
        Write-Host "响应内容: $rawContent"  
  
        # 检查 Content-Type  
        if ($response.Headers["Content-Type"]) {  
            $contentType = $response.Headers["Content-Type"]  
            Write-Host "Content-Type: $contentType"  
        } else {  
            Write-Host "Content-Type header is missing."  
        }  
    } catch {  
        Write-Host "发生错误: $_"  
    }  
}  