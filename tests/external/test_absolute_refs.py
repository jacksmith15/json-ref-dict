from json_ref_dict import RefDict


def test_absolute_references_are_detected():
    url = "http://json.schemastore.org/azure-iot-edge-deployment-template-2.0"
    ref_dict = RefDict(url)
    assert ref_dict["definitions"]["moduleType"] == RefDict(
        "http://json.schemastore.org/azure-iot-edge-deployment-2.0#"
        "/definitions/moduleType"
    )
