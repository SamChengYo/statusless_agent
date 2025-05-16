import os
import shutil
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from data_pipeline.storage_operate import S3StorageOperate, MinioStorageOperate
from data_pipeline.file_processor import DocumentProcessor
import os
import glob

app = FastAPI()

@app.post("/process-files")
async def process_files(
    files: list[UploadFile] = File(...),
    mode: str = Form(...),
    bucket_name: str = Form(...)
):
    upload_paths = []
    os.makedirs("uploads", exist_ok=True)

    for file in files:
        temp_path = os.path.join("uploads", file.filename)
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        upload_paths.append((file.filename, temp_path))

    if mode.lower() == "minio":
        storage = MinioStorageOperate(
            endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            bucket_name=bucket_name,
            secure=os.getenv("MINIO_USE_HTTPS", "false").lower() == "true"
        )
    else:
        storage = S3StorageOperate(bucket_name=bucket_name)

    processor = DocumentProcessor(
        storage_instance=storage,
        split_dir="data_pipeline/splits",
        md_dir="data_pipeline/md",
        img_dir="data_pipeline/images"
    )

    files_status_list = []
    for filename, _ in upload_paths:
        files_status_list.append({
            "filename": filename,
            "status": "queued",
            "message": "Not started",
            "urls": [],
            "current_page": None
        })

    async def event_stream():
        yield f"data: {json.dumps({'status': 'running', 'files': files_status_list})}\n\n"
        
        for file_status, (filename, temp_path) in zip(files_status_list, upload_paths):
            file_status["status"] = "processing"
            file_status["message"] = f"Start processing file: {filename}"

            yield f"data: {json.dumps({'status': 'running', 'files': files_status_list})}\n\n"

            try:
                for result in processor.process_file_streaming(temp_path):
                    if "error" in result:
                        file_status["status"] = "error"
                        file_status["message"] = result["error"]

                        yield f"data: {json.dumps({'status': 'running', 'files': files_status_list})}\n\n"
                        break
                    else:
                        file_status["current_page"] = result["part"]
                        file_status["message"] = result["message"]
                        file_status["urls"].append(result["url"])

                        yield f"data: {json.dumps({'status': 'running', 'files': files_status_list})}\n\n"

                if file_status["status"] != "error":
                    file_status["status"] = "success"
                    file_status["message"] = f"File {filename} processed successfully"

                    yield f"data: {json.dumps({'status': 'running', 'files': files_status_list})}\n\n"

            except Exception as e:
                file_status["status"] = "error"
                file_status["message"] = f"Unexpected error: {str(e)}"

                yield f"data: {json.dumps({'status': 'running', 'files': files_status_list})}\n\n"
                
            # 🧹 處理完一個檔案就清理相關的暫存檔案
            base_name, _ = os.path.splitext(filename)  # 只取掉副檔名的「檔案名」

            # 刪除 md/
            md_pattern = os.path.join("data_pipeline/md", f"{base_name}_*.md")
            for md_file in glob.glob(md_pattern):
                try:
                    os.remove(md_file)
                except Exception as e:
                    print(f"Failed to delete {md_file}: {e}")

            # 刪除 splits/
            split_pattern = os.path.join("data_pipeline/splits", f"{base_name}_*.pdf")
            for split_file in glob.glob(split_pattern):
                try:
                    os.remove(split_file)
                except Exception as e:
                    print(f"Failed to delete {split_file}: {e}")

            # 刪除 uploads/
            upload_file_path = os.path.join("uploads", filename)
            if os.path.exists(upload_file_path):
                try:
                    os.remove(upload_file_path)
                except Exception as e:
                    print(f"Failed to delete {upload_file_path}: {e}")

        yield f"data: {json.dumps({'status': 'done', 'files': files_status_list})}\n\n"
        

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)