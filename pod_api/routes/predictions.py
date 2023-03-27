import io
import json
from typing import Union

import numpy as np
import requests
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Security,
    status,
)
from fastapi import Body
from keras.applications.vgg16 import preprocess_input
from pydantic import BaseModel, Field

# from keras.preprocessing import image
from routes.quries_s3 import get_s3_object, resolve_s3_path
from quries import get_signatory_list, get_signatory
from sagemaker.predictor import Predictor
from sqlalchemy.orm import Session
from tensorflow.keras.preprocessing import image
from sagemaker.predictor import Predictor

endpoint_name = "pod-endpoint"

router = APIRouter()


def process_s3_image(url):
    url, s3_key, s3_uri, extention, file_name = resolve_s3_path(url)
    byte_image = get_s3_object(s3_key)
    io_obj = io.BytesIO(byte_image.read())
    raw_image = image.load_img(io_obj, target_size=(224, 224))

    x = image.img_to_array(raw_image)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    input_data = {
        "instances": x.tolist(),
    }
    res = json.dumps(input_data)
    return res

    return data

    # image_path: Union[str, None] = Query(default="https://winsport-node.s3.amazonaws.com/55d88e35-adbf-4d72-9cf8-def025e965ba/signatures/b89b3b17-eb5e-4812-850e-d8532cbb6e2f/1675927786242b89b3b17-eb5e-4812-850e-d8532cbb6e2foriginal_4_1.png",alias="image-path"),
    # signatory_uuid: Union[str, None] = Query(default='b89b3b17-eb5e-4812-850e-d8532cbb6e2f',alias="signatory-uuid"),
@router.post("/")
def get_prediciton(

    image_path: Union[str, None] = Body(),
    signatory_uuid: Union[str, None] = Body(),

    ):
    # try:
        if not image_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image path can't be empty",
            )

        data = process_s3_image(image_path)
        headers = {"ContentType": "application/json"}
        # data = image_file_to_tensor()


        endpoint_name = "pod-endpoint"
        predictor = Predictor(endpoint_name=endpoint_name)
        results = predictor.predict(data, initial_args=headers)
        data = json.loads(results)
        feature = data['predictions'][0]
        # print(type(feature))
        list_1 = feature
        # print(list_1)
        max_value = max(feature)
        max_index = list_1.index(max_value)
        print(max_index)
        signatory_list = get_signatory_list()
        signatory_id = signatory_list[max_index]

        print(signatory_id, "---------------->", signatory_uuid)

        if signatory_uuid == signatory_id:
            return {"status": status.HTTP_200_OK, "data": max_index, "signatory_uuid": signatory_uuid, "message": "Approved"}
        else:
            resp = get_signatory(signatory_uuid)
            if resp:
                # return {"status": status.HTTP_401_UNAUTHORIZED, "data": max_index, "signatory_uuid": signatory_uuid, "message": "Signatory Not Trained/Present"}
                detail="Signatory Not Trained/Present"
            else:
                detail="Not Varified"

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        # print(data)
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Internal Server Error due to {e}",
    #     )
