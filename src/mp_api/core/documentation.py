# noqa: E501
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
        "name": "Summary",
        "description": "Route providing a large amount of amalgamated data for a material. This is constructed by \
            combining subsets of data from many of the other API endpoints. The summary endpoint is very useful for \
            performing queries for materials over a large property space. Note that every unique material within \
            the Materials Project should have a set of summary data. See the `SummaryDoc` schema for a full list of \
            fields returned by this route.",
    },
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
        "description": "Route providing computed thermodynamic data for a material such as \
            formation energy and energy above hull. Corrected energy values are also available that employ \
            the schemes discussed by \
            [Jain *et al.*](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.84.045115) \
            and [Wang *et al.*](https://chemrxiv.org/engage/chemrxiv/article-details/60c758d9469df42a4ef45757)\
            See the `ThermoDoc` schema for a full list of fields returned by this route.",
        "externalDocs": {
            "description": "For a more detailed description",
            "url": "https://docs.materialsproject.org/methodology/total-energies",
        },
    },
    {
        "name": "Dielectric",
        "description": "Route providing computed dielectric data for a material following the \
            methodology discussed by [Petousis *et al.*](https://doi.org/10.1038/sdata.2016.134) \
            Note that dielectric data has not been calculated for all materials in the Materials \
            Project database. See the `DielectricDoc` schema for a full list of fields returned by this route.",
        "externalDocs": {
            "description": "For a more detailed description",
            "url": "https://docs.materialsproject.org/methodology/dielectricity",
        },
    },
    {
        "name": "Magnetism",
        "description": "Route providing computed magnetic ordering related data for a material following the \
            methodology discussed by [Horton *et al.*](https://doi.org/10.1038/s41524-019-0199-7) \
            Note that magnetic data has not been calculated for all materials in the Materials \
            Project database. See the `MagnetismDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Piezoelectric",
        "description": "Route providing computed piezoelectric data for a material following the \
            methodology discussed by [de Jong *et al.*](https://doi.org/10.1038/sdata.2015.53) \
            Note that piezoelectric data has not been calculated for all materials in the Materials \
            Project database. See the `PiezoDoc` schema for a full list of fields returned by this route.",
        "externalDocs": {
            "description": "For a more detailed description",
            "url": "https://docs.materialsproject.org/methodology/piezoelectricity",
        },
    },
    {
        "name": "Phonon",
        "description": "Route providing computed phonon data for a material following the \
            methodology discussed by [Petretto *et al.*](https://doi.org/10.1038/sdata.2018.65) \
            Note that phonon data has not been calculated for all materials in the Materials \
            Project database. See the `PhononBSDOSDoc` schema for a full list of fields returned by this route.",
        "externalDocs": {
            "description": "For a more detailed description",
            "url": "https://docs.materialsproject.org/methodology/phonons",
        },
    },
    {
        "name": "EOS",
        "description": "Route providing computed equations of state data for a material following the \
            methodology discussed by [Latimer *et al.*](https://doi.org/10.1038/s41524-018-0091-x) \
            Note that equations of state data has not been calculated for all materials in the Materials \
            Project database. See the `EOSDoc` schema for a full list of fields returned by this route.",
        "externalDocs": {
            "description": "For a more detailed description",
            "url": "https://docs.materialsproject.org/methodology/equations-of-state",
        },
    },
    {
        "name": "Similarity",
        "description": "Route providing a computed similarity metric between materials following the \
            methodology discussed by Zimmerman *et al.* in [10.3389/fmats.2017.00034](https://doi.org/10.3389/fmats.2017.00034) \
            and [10.1039/C9RA07755C](https://doi.org/10.1039/C9RA07755C). \
            Note that similarity data has not been calculated for all materials in the Materials \
            Project database. See the `imilarityDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "XAS",
        "description": "Route providing computed x-ray absorption spectroscopy data for a material following the \
            methodology discussed by [Mathew *et al.*](https://doi.org/10.1038/sdata.2018.151) \
            and [Chen *et al.*](https://doi.org/10.1038/s41597-021-00936-5) \
            Note that x-ray absorption spectroscopy data has not been calculated for all materials in the Materials \
            Project database. See the `XASDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Grain Boundaries",
        "description": "Route providing computed grain boundary data for a material following the \
            methodology discussed by [Hui *et al.*](https://doi.org/10.1016/j.actamat.2019.12.030) \
            Note that grain boundary data has not been calculated for all materials in the Materials \
            Project database. See the `GrainBoundaryDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Electronic Structure",
        "description": "Routes providing computed electronic structure related data for a material such as \
            band gap and fermi level. Python objects for line-mode band structures, density of states, and \
            fermi surfaces are also available. This data was obtained following the methodology discussed by \
            [Munro *et al.*](https://doi.org/10.1038/s41524-020-00383-7) and [Ganose *et al.*](https://doi.org/10.21105/joss.03089) \
            Note that full band structure, density of states, and fermi surface data has not been calculated for \
            all materials in the Materials Project database. See the `ElectronicStructureDoc` and `FermiDoc` schema \
            for a full list of fields returned by the associated routes.",
        "externalDocs": {
            "description": "For a more detailed description",
            "url": "https://docs.materialsproject.org/methodology/electronic-structure",
        },
    },
    {
        "name": "Elasticity",
        "description": "Route providing computed elasticity data for a material following the \
            methodology discussed by [de Jong *et al.*](https://doi.org/10.1038/sdata.2015.9) \
            Note that elasticity data has not been calculated for all materials in the Materials \
            Project database. See the `ElasticityDoc` schema for a full list of fields returned by this route.",
        "externalDocs": {
            "description": "For a more detailed description",
            "url": "https://docs.materialsproject.org/methodology/elasticity",
        },
    },
    {
        "name": "DOIs",
        "description": "Route providing DOI and bibtex reference information for a material. \
            Note that this data may not be available for all materials in the Materials \
            Project database. See the `DOIDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Substrates",
        "description": "Route providing computed suggested substrate data for a material following the \
            methodology discussed by [Ding *et al.*](https://doi.org/10.1021/acsami.6b01630) \
            Note that substrate data has not been calculated for all materials in the Materials \
            Project database. See the `SubstratesDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Surface Properties",
        "description": "Route providing computed surface property data for a material following the \
            methodology discussed by [Tran *et al.*](https://doi.org/10.1038/sdata.2016.80) \
            Note that surface data has not been calculated for all materials in the Materials \
            Project database. See the `SurfacePropDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Robocrystallographer",
        "description": "Route providing a computed text description for a material following the \
            methodology discussed by [Ganose *et al.*](https://doi.org/10.1557/mrc.2019.94) \
            Note that descriptions may not been calculated for all materials in the Materials \
            Project database. See the `RobocrysDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Synthesis",
        "description": "Route providing a synthesis recipes for materials extracted from literature \
            following the methodology discussed by [Kononova *et al.*](https://doi.org/10.1038/s41597-019-0224-1) \
            Note that synthesis recipes may not be available for all materials in the Materials \
            Project database. See the `SynthesisSearchResultModel` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Electrodes",
        "description": "Route providing computed electrode data for a material following the \
            methodology discussed by [Shen *et al.*](https://doi.org/10.1038/s41524-020-00422-3) \
            Note that electrode data has not been calculated for all materials in the Materials \
            Project database. See the `InsertionElectrodeDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Molecules",
        "description": "Route providing computed data for a molecule such as charge, \
            electron affinity, and ionization energy. The unique identifier for a molecule \
            is its `task_id` (e.g. `mol-45807`). See the `MoleculesDoc` schema for a full list of \
            fields returned by this route.",
    },
    {
        "name": "Oxidation States",
        "description": "Route providing computed oxidation state data for a material following the \
            methodology employed by the [BVAnalyzer](https://pymatgen.org/pymatgen.analysis.bond_valence.html) \
            in Pymatgen. Note that oxidation state data has not been calculated for all materials in the Materials \
            Project database. See the `OxidationStateDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "Provenance",
        "description": "Route providing provenance data for a material such as whether it is theoretical, \
            its associated ICSD entries, and relevant references in literature. Note that provenance data \
            may not be available for all materials in the Materials Project database. See the `ProvenanceDoc` \
            schema for a full list of fields returned by this route.",
    },
    {
        "name": "Charge Density",
        "description": "Route providing computed charge density data for a material following the \
            methodology discussed by [Shen *et al.*](https://arxiv.org/abs/2107.03540). Please email \
            <heavy.api.use@materialsproject.org> if you would like to retrieve a large amount of this data. \
            Note that charge densities may not be calculated for all materials in the Materials \
            Project database. See the `ChgcarDataDoc` schema for a full list of fields returned by this route.",
    },
    {
        "name": "MPComplete",
        "description": "Route for submitting structures to the Materials Project. If calculations are run with the \
            submitted structure, the submitter will be credited with the submitted public name and email.",
    },
]

