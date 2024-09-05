import requests


def upload_document(file, id_role):
    # URL endpoint Django untuk upload file
    url = "http://127.0.0.1:8000/api/doc/upload"

    # File dan data lain yang ingin dikirim
    if file is not None:
        file_path = file.getvalue()
        id_role = id_role

        data = {
                'id_role': id_role  
        }

            # Kirim POST request dengan file dan data
        response = requests.post(
            url,
            data=data,
            files={"file" : (file.name, file_path, 'application/pdf')}
            )
        
        # Cek status dan response
        if response.status_code == 201:
            print("File berhasil diupload!")
            print(response.json()) 
            return response.json()
        else:
            print(f"Gagal upload file. Status code: {response.status_code}")
            print(response.text)
            return response.json()      
    else:
        return "file is None"      