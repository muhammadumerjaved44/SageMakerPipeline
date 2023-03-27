import json

from models import PodModel, SignaturiesModel, TrainedSignaturiesModel

from routes.quries_s3 import move_file_s3
from datetime import datetime


def get_pod_files_by_id(pod_id):
    pod_obj = PodModel.objects.filter(uei=pod_id).get()
    pod_data = json.loads(pod_obj.to_json())
    path_list = []
    if "bolPath" in pod_data:
        path_list.append(pod_data["bolPath"])
    if "podPath" in pod_data:
        path_list.append(pod_data["podPath"])
    if "invoicePath" in pod_data:
        path_list.append(pod_data["invoicePath"])
    return path_list


def update_pod_watermark_url(pod_id, data):

    print(data, "update ------------>", pod_id)

    pod_obj = PodModel.objects(uei=pod_id).modify(**data, upsert=True)


def get_s3_object_key(url):
    # Split the URL into parts using '/' as a separator
    parts = url.split('/')

    # Find the index of the first part that starts with 's3.amazonaws.com'
    index = [i for i, part in enumerate(parts) if part.startswith('winsport-node.s3.amazonaws.com')][0]

    # Return the object key by joining the parts after the index
    return '/'.join(parts[index + 1:])


def get_s3_sub_object_key(key):
    # Split the URL into parts using '/' as a separator
    parts = key.split('/')

    # Find the index of the first part that starts with 's3.amazonaws.com'
    index = [i for i, part in enumerate(parts) if part.startswith('signatures')][0]

    # Return the object key by joining the parts after the index
    return 'signatures/'+'/'.join(parts[index + 1:])


def get_s3_dataset_object_key(key):
    # Split the URL into parts using '/' as a separator
    parts = key.split('/')

    # Find the index of the first part that starts with 's3.amazonaws.com'
    index = [i for i, part in enumerate(parts) if part.startswith('signatures')][0]

    # Return the object key by joining the parts after the index
    return 'dataset/'+'/'.join(parts[index + 1:])


def upsert_trained_signatories(data):
    trained_signatories = TrainedSignaturiesModel.objects(signatory_id=data['signatory_id']).update_one(
        is_added_to_signatures = data["is_added_to_signatures"],
        signatues_s3_keys = data["signatues_s3_keys"],
        created_at = datetime.utcnow(),
        upsert=True
    )


def upsert_trained_dataset(data):
    trained_signatories = TrainedSignaturiesModel.objects(signatory_id=data['signatory_id']).update_one(
        is_data_set_created = data['is_data_set_created'],
        dataset_s3_keys = data['dataset_s3_keys'],
        upsert=True
    )

def move_to_signatures():

    signaturies = SignaturiesModel.objects.filter(isTrain=False).all()
    for signaturs in signaturies:
        signatues_s3_keys = []
        for signature in signaturs.signature:
            key = get_s3_object_key(signature)
            print(signaturs.uuid, key)
            signatury_key = get_s3_sub_object_key(key)
            signatues_s3_keys.append(signatury_key)
            move_file_s3('winsport-node', key, 'winsport-signatures-dev', signatury_key)

        data = {
            "signatory_id": f'{signaturs.uuid}',
            "signatues_s3_keys": signatues_s3_keys,
            "is_added_to_signatures": True,
            "is_data_set_created": False,
        }

        upsert_trained_signatories(data)

def move_to_dateset():

    signaturies = TrainedSignaturiesModel.objects.filter(is_added_to_signatures=True).all()
    for signaturs in signaturies:
        dataset_s3_keys = []
        signaturs
        for key in signaturs.signatues_s3_keys:
            dataset_key = get_s3_dataset_object_key(key)
            # print(dataset_key)
            dataset_s3_keys.append(dataset_key)
            move_file_s3('winsport-signatures-dev', key, 'winsport-signatures-dev', dataset_key)

        data = {
            "signatory_id": f'{signaturs.signatory_id}',
            "is_data_set_created": True,
            "dataset_s3_keys": dataset_s3_keys,
        }
        # print(data)
        upsert_trained_dataset(data)

    return signaturies


def update_trained_signatory_flag(signaturies, flag):
   for signatory in signaturies:
        print(signatory.signatory_id)
        TrainedSignaturiesModel.objects(signatory_id=signatory.signatory_id).update_one(
            is_trained = flag,
            upsert=True
        )


def get_signatory_list():
    signaturies = TrainedSignaturiesModel.objects().order_by('+created_at')
    signatory_list = []
    for signatory in signaturies:
        print(signatory.signatory_id)
        signatory_list.append(signatory.signatory_id)

    return signatory_list


def get_signatory(signatory_id="b89b3b17-eb5e-4812-850e-d8532cbb6e2e"):
    signaturies = TrainedSignaturiesModel.objects(signatory_id=signatory_id).first()

    if signaturies:
        return signaturies
    else:
        return False

