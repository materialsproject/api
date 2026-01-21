from mp_api.client.routes.materials.doi import DOIRester

from ..conftest import client_search_testing, requires_api_key


@requires_api_key
def test_doi_search():
    with DOIRester() as rester:
        client_search_testing(
            search_method=rester.search,
            excluded_params=[
                "num_chunks",
                "chunk_size",
                "all_fields",
                "fields",
            ],
            alt_name_dict={
                "material_ids": "material_id",
            },
            custom_field_tests={
                "material_ids": ["mp-149", "mp-13"],
                "material_ids": "mp-149",
            },
            sub_doc_fields=[],
        )
