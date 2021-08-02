description = """
The Materials Project API allows anyone to have direct access to current, up-to-date information from the Materials Project database in a structured way.

This allows for analysis, development of automated tools, machine learning, downloading personal copies of the Materials Project database and more on a large scale.

The API is offered with the hopes of making Materials Project data more useful to you. We want you to use our data! As such, the API is offered free-of-charge and we support several tools to help you get started.

## API Key
To make any request to the Materials Project API, you must use an API key. Your API key is generated for you automatically upon registering with the Materials Project website and is synced with the email you used to register.

Remember to keep your API key safe and to not share it with anyone you do not trust.

If you are logged in, you can always access your API key from this page or from your [dashboard](https://next-gen.materialsproject.org/dashboard).

If you intend heavy API usage, you can give us a heads up by sending a message to <heavy.api.use@materialsproject.org>. With the exception of retrieving charge densities, this is not required, but may help us if we see unusual load on our servers.

## Accessing Data
To use the API, you have three options:

1. You can use our first-party supported Python client. This is the recommend route. The client is pip installable.

    ```
    pip install mp-api
    ```

    The `MPRester` client can the be accessed through this package. This will ultimately replace the legacy `MPRester` available in pymatgen. 
    
    For more details on how to use this, including code examples, please see <https://next-gen.materialsproject.org/api>.

2. You can demo the API interactively on this documentation page. Click the "Authorize" button, paste in your API key, and then click the appropriate section to try out a query.

3. Since this is a REST API, and offers a fully-compliant OpenAPI specification, it's possible to use the API with many libraries in many languages and environments, including JavaScript, MATLAB, Mathematica, etc. However, we do not offer first-party support for explaining how to do this, and you will have to follow the specification yourself.

"""

tags_meta = [
    {
        "name": "Materials",
        "description": "Core endpoints for data associated with each unique material in the Materials Project database defined by `material_id`. Root level data is defined by `MaterialsDoc` schema.",
    },
    {
        "name": "Tasks",
        "description": "Core endpoints for data associated with each unique calculation in the Materials Project database defined by `task_id`. Root level data is defined by `TaskDoc` schema.",
    },
    {
        "name": "Thermo",
        "description": "Endpoints for thermodynamic data associated with each unique material in the Materials Project database defined by `material_id`. Root level data is defined by `ThermoDoc` schema.",
    },
    {
        "name": "Dielectric",
        "description": "Endpoints for dielectric data associated with each unique material in the Materials Project database defined by `material_id`. Root level data is defined by `DielectricDoc` schema.",
    },
    {
        "name": "Magnetism",
        "description": "Endpoints for magnetic data associated with each unique material in the Materials Project database defined by `material_id`. Root level data is defined by `MagnetismDoc` schema.",
    },
    {
        "name": "Piezoelectric",
        "description": "Endpoints for piezoelectric data associated with each unique material in the Materials Project database defined by `material_id`. Root level data is defined by `PiezoDoc` schema.",
    },
]

