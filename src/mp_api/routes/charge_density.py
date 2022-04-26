import zlib
from os import environ
from pathlib import Path
from typing import Dict, List, Optional, Union

import boto3
import msgpack
from botocore import UNSIGNED
from botocore.client import Config
from botocore.exceptions import ConnectionError

try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal  # type: ignore

from emmet.core.charge_density import ChgcarDataDoc
from monty.serialization import MontyDecoder, dumpfn
from mp_api.core.client import BaseRester


class ChargeDensityRester(BaseRester[ChgcarDataDoc]):

    suffix = "charge_density"
    primary_key = "fs_id"
    document_model = ChgcarDataDoc  # type: ignore
    boto_resource = None

    def download_for_task_ids(
        self,
        path: str,
        task_ids: List[str],
        ext: Literal["json.gz", "json", "mpk", "mpk.gz"] = "json.gz",  # type: ignore
    ) -> int:
        """
        Download a set of charge densities.

        :param path: Your local directory to save the charge densities to. Each charge
        density will be serialized as a separate JSON file with name given by the relevant
        task_id.
        :param task_ids: A list of task_ids.
        :param ext: Choose from any file type supported by `monty`, e.g. json or msgpack.
        :return: An integer for the number of charge densities saved.
        """
        num_downloads = 0
        path_obj = Path(path)
        chgcar_summary_docs = self.search(task_ids=task_ids)
        for entry in chgcar_summary_docs:
            fs_id = entry.fs_id  # type: ignore
            task_id = entry.task_id  # type: ignore
            doc = self.get_data_by_id(fs_id)
            dumpfn(doc, path_obj / f"{task_id}.{ext}")
            num_downloads += 1
        return num_downloads

    def search(  # type: ignore
        self, num_chunks: Optional[int] = 1, chunk_size: int = 10, **kwargs
    ) -> Union[List[ChgcarDataDoc], List[Dict]]:  # type: ignore
        """
        A search method to find what charge densities are available via this API.

        Arguments:
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.

        Returns:
            A list of ChgcarDataDoc that contain task_id references.
        """

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=False,
            fields=["last_updated", "task_id", "fs_id"],
            **kwargs,
        )

    def get_charge_density_from_file_id(self, fs_id: str):
        url_doc = self.get_data_by_id(fs_id)

        if url_doc:

            # The check below is performed to see if the client is being
            # used by our internal AWS deployment. If it is, we pull charge
            # density data from a private S3 bucket. Else, we pull data
            # from public MinIO buckets.
            if environ.get("AWS_EXECUTION_ENV", None) == "AWS_ECS_FARGATE":

                if self.boto_resource is None:
                    self.boto_resource = self._get_s3_resource(
                        use_minio=False, unsigned=False
                    )

                bucket, obj_prefix = self._extract_s3_url_info(url_doc, use_minio=False)

            else:
                try:
                    if self.boto_resource is None:
                        self.boto_resource = self._get_s3_resource()

                    bucket, obj_prefix = self._extract_s3_url_info(url_doc)

                except ConnectionError:
                    self.boto_resource = self._get_s3_resource(use_minio=False)

                    bucket, obj_prefix = self._extract_s3_url_info(
                        url_doc, use_minio=False
                    )

            r = self.boto_resource.Object(  # type: ignore
                bucket, "{}/{}".format(obj_prefix, url_doc.fs_id)
            ).get()["Body"]

            packed_bytes = r.read()

            packed_bytes = zlib.decompress(packed_bytes)
            json_data = msgpack.unpackb(packed_bytes, raw=False)
            chgcar = MontyDecoder().process_decoded(json_data["data"])

            return chgcar

        else:
            return None

    def _extract_s3_url_info(self, url_doc, use_minio: bool = True):

        if use_minio:
            url_list = url_doc.url.split("/")
            bucket = url_list[3]
            obj_prefix = url_list[4]
        else:
            url_list = url_doc.s3_url_prefix.split("/")
            bucket = url_list[2].split(".")[0]
            obj_prefix = url_list[3]

        return (bucket, obj_prefix)

    def _get_s3_resource(self, use_minio: bool = True, unsigned: bool = True):

        resource = boto3.resource(
            "s3",
            endpoint_url="https://minio.materialsproject.org" if use_minio else None,
            config=Config(signature_version=UNSIGNED) if unsigned else None,
        )

        return resource
