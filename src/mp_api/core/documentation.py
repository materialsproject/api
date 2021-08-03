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

1. You can use our first-party supported Python client. This is the recommend route. The `mp-api` package containing the client is pip installable.

    ```
    pip install mp-api
    ```

    The `MPRester` client can be accessed by importing from it. This will ultimately replace the legacy `MPRester` available in pymatgen.
    
    For more details on how to use this, including code examples, please see <https://next-gen.materialsproject.org/api>.

2. You can demo the API interactively on this documentation page. Click the "Authorize" button, paste in your API key, and then click the appropriate section to try out a query.

3. Since this is a REST API, and offers a fully-compliant OpenAPI specification, it's possible to use the API with many libraries in many languages and environments, including JavaScript, MATLAB, Mathematica, etc. However, we do not offer first-party support for explaining how to do this, and you will have to follow the specification yourself.

"""

tags_meta = [
    {
        "name": "Materials",
        "description": 'Route for "core" information associated with a given material in the Materials Project \
            database. The unique identifier for a material is its `material_id` (e.g. `mp-149`). Core data in \
            this context refers to the crystal structure, information associated with it such as the density \
            and chemical formula, and the associated calculations which are identified with unique `task_id` \
            values. It does not contain any materials properties such as the formation energy or band gap, please \
            consult other property-specific endpoints for this information. See the `MaterialsDoc` schema for \
            a full list of fields returned by this route.',
    },
    {
        "name": "Tasks",
        "description": 'Route for "core" information associated with a given calculation in the Materials Project \
            database. Multiple calculations can ultimately be associated with a unique material, and are the source \
            of its reported properties. The unique identifier for a calculation is its `task_id`. Note \
            that the `material_id` chosen for a given material is sourced from one of the `task_id` values \
            associated with it. Core data in this context refers to calculation quantities such as parsed input \
            and output data (e.g. VASP input flags, atomic forces, structures) and runtime statistics. See the \
            `TaskDoc` schema for a full list of fields returned by this route.',
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

