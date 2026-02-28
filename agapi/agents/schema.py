TOOLS_SCHEMA = [
    # JARVIS-DFT
    {
        "type": "function",
        "function": {
            "name": "query_by_formula",
            "description": "Get all polymorphs of a chemical formula from JARVIS-DFT (e.g., SiC, GaN, MgB2)",
            "parameters": {
                "type": "object",
                "properties": {
                    "formula": {
                        "type": "string",
                        "description": "Chemical formula",
                    }
                },
                "required": ["formula"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_by_elements",
            "description": "Find materials containing specific elements (e.g., 'Si,C')",
            "parameters": {
                "type": "object",
                "properties": {
                    "elements": {
                        "type": "string",
                        "description": "Comma-separated elements",
                    }
                },
                "required": ["elements"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_by_jid",
            "description": "Get detailed info for a JARVIS ID (e.g., 'JVASP-1002')",
            "parameters": {
                "type": "object",
                "properties": {
                    "jid": {"type": "string", "description": "JARVIS ID"}
                },
                "required": ["jid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_by_property",
            "description": "Find materials by property range (e.g., bandgap 2-3 eV)",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_name": {"type": "string"},
                    "min_val": {"type": "number"},
                    "max_val": {"type": "number"},
                    "elements": {"type": "string"},
                },
                "required": ["property_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_extreme",
            "description": "Find material with max/min property value",
            "parameters": {
                "type": "object",
                "properties": {
                    "property_name": {"type": "string"},
                    "maximize": {"type": "boolean"},
                    "elements": {"type": "string"},
                    "formula": {"type": "string"},
                    "constraint_property": {"type": "string"},
                    "min_constraint": {"type": "number"},
                    "max_constraint": {"type": "number"},
                },
                "required": ["property_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_supercell",
            "description": "Create a supercell from a POSCAR structure by replicating the unit cell. Use this to create larger simulation cells for defect studies or interface calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string",
                    },
                    "scaling_matrix": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of 3 integers [nx, ny, nz] for supercell dimensions. Example: [2,1,1] creates 2x1x1 supercell",
                        "minItems": 3,
                        "maxItems": 3,
                    },
                },
                "required": ["poscar", "scaling_matrix"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "substitute_atom",
            "description": "Substitute (replace) atoms in a structure. For example, replace Ga with Al to study doping or alloy formation. Useful for creating substitutional defects or alloy structures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string",
                    },
                    "element_from": {
                        "type": "string",
                        "description": "Element to replace (e.g., 'Ga', 'Si', 'N')",
                    },
                    "element_to": {
                        "type": "string",
                        "description": "Element to substitute with (e.g., 'Al', 'Ge', 'P')",
                    },
                    "num_substitutions": {
                        "type": "integer",
                        "description": "Number of atoms to substitute (default: 1)",
                        "default": 1,
                    },
                },
                "required": ["poscar", "element_from", "element_to"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_vacancy",
            "description": "Create vacancy defects by removing atoms from a structure. Useful for studying point defects, defect formation energies, or creating porous structures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string",
                    },
                    "element": {
                        "type": "string",
                        "description": "Element to remove to create vacancy (e.g., 'Ga', 'Si', 'O')",
                    },
                    "num_vacancies": {
                        "type": "integer",
                        "description": "Number of atoms to remove (default: 1)",
                        "default": 1,
                    },
                },
                "required": ["poscar", "element"],
            },
        },
    },
    # ALIGNN
    {
        "type": "function",
        "function": {
            "name": "alignn_predict",
            "description": "Predict material properties using ALIGNN machine learning models. Predicts formation energy, bandgap (OptB88vdW and MBJ), elastic moduli (bulk and shear), piezoelectric properties, and superconducting critical temperature. Can accept either a POSCAR structure string or a JARVIS-ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string. Required if jid is not provided. Contains lattice vectors, atomic species, and atomic positions.",
                    },
                    "jid": {
                        "type": "string",
                        "description": "JARVIS-ID (e.g., 'JVASP-1002', 'JVASP-816'). If provided, the structure will be fetched from JARVIS database and poscar parameter will be ignored. Use this when you know the JARVIS-ID of the material.",
                    },
                },
                "required": [
                    "poscar"
                ],  # poscar is required by the function signature, but jid can override it
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "alignn_ff_relax",
            "description": "Relax structure using ALIGNN force field",
            "parameters": {
                "type": "object",
                "properties": {"poscar": {"type": "string"}},
                "required": ["poscar"],
            },
        },
    },
    # SlakoNet
    {
        "type": "function",
        "function": {
            "name": "slakonet_bandstructure",
            "description": "Calculate electronic band structure and density of states using SlakoNet tight-binding model. Returns band gap, VBM, CBM values AND a band structure plot image. Works best for structures with ≤10 atoms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string",
                    },
                    "energy_range_min": {
                        "type": "number",
                        "description": "Minimum energy for plot in eV (default: -8.0)",
                        "default": -8.0,
                    },
                    "energy_range_max": {
                        "type": "number",
                        "description": "Maximum energy for plot in eV (default: 8.0)",
                        "default": 8.0,
                    },
                },
                "required": ["poscar"],
            },
        },
    },
    # DiffractGPT
    {
        "type": "function",
        "function": {
            "name": "diffractgpt_predict",
            "description": "Predict structure from XRD peaks (format: '30.42(1.0),49.02(0.49)')",
            "parameters": {
                "type": "object",
                "properties": {
                    "formula": {"type": "string"},
                    "peaks": {
                        "type": "string",
                        "description": "XRD peaks as '2theta(intensity),...'",
                    },
                },
                "required": ["formula", "peaks"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "xrd_match",
            "description": "Match experimental XRD to database",
            "parameters": {
                "type": "object",
                "properties": {
                    "formula": {"type": "string"},
                    "xrd_pattern": {"type": "string"},
                },
                "required": ["formula", "xrd_pattern"],
            },
        },
    },
    # Protein
    {
        "type": "function",
        "function": {
            "name": "protein_fold",
            "description": "Predict 3D protein structure from amino acid sequence using ESMFold AI. Input is a sequence of one-letter amino acid codes (e.g., 'MKTA...VSLL'). Returns PDB format structure with atomic coordinates. Works for sequences 10-400 amino acids long. ESMFold is a state-of-the-art AI model that predicts protein structure from sequence alone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Amino acid sequence using one-letter codes: A (Ala), R (Arg), N (Asn), D (Asp), C (Cys), Q (Gln), E (Glu), G (Gly), H (His), I (Ile), L (Leu), K (Lys), M (Met), F (Phe), P (Pro), S (Ser), T (Thr), W (Trp), Y (Tyr), V (Val). Remove any whitespace or line breaks.",
                    }
                },
                "required": ["sequence"],
            },
        },
    },
    # XRD
    {
        "type": "function",
        "function": {
            "name": "generate_xrd_pattern",
            "description": "Generate powder X-ray diffraction (XRD) pattern from crystal structure. Simulates XRD experiment and returns peak positions (2θ), intensities, and d-spacings. Useful for predicting what XRD pattern a structure would produce, comparing theoretical vs experimental patterns, or generating training data. Returns DiffractGPT-compatible description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string containing lattice vectors, atom positions, and elements",
                    },
                    "wavelength": {
                        "type": "number",
                        "description": "X-ray wavelength in Angstroms. Common values: 1.54184 (Cu K-alpha, default), 1.54056 (Cu K-alpha1), 0.71073 (Mo K-alpha)",
                        "default": 1.54184,
                    },
                    "num_peaks": {
                        "type": "integer",
                        "description": "Number of strongest peaks to report in summary (default: 20)",
                        "default": 20,
                    },
                    "theta_range": {
                        "type": "array",
                        "description": "2-theta range in degrees [min, max]. Default: [0, 90]",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "required": ["poscar"],
            },
        },
    },
    # Intermat
    {
        "type": "function",
        "function": {
            "name": "generate_interface",
            "description": "Generate heterostructure interface between two materials (film on substrate). Creates interface by matching lattice parameters and stacking specified crystal surfaces.",
            "parameters": {
                "type": "object",
                "properties": {
                    "film_poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string for the film material (top layer)",
                    },
                    "substrate_poscar": {
                        "type": "string",
                        "description": "POSCAR format structure string for the substrate material (bottom layer)",
                    },
                    "film_indices": {
                        "type": "string",
                        "description": "Miller indices for film surface, format: 'h_k_l' with underscores. Common: '0_0_1' (001), '1_1_1' (111), '1_0_0' (100)",
                        "default": "0_0_1",
                    },
                    "substrate_indices": {
                        "type": "string",
                        "description": "Miller indices for substrate surface, format: 'h_k_l' with underscores",
                        "default": "0_0_1",
                    },
                    "film_thickness": {
                        "type": "number",
                        "description": "Film layer thickness in Angstroms. Typical: 10-30 Å",
                        "default": 16,
                    },
                    "substrate_thickness": {
                        "type": "number",
                        "description": "Substrate layer thickness in Angstroms. Typical: 10-30 Å",
                        "default": 16,
                    },
                    "separation": {
                        "type": "number",
                        "description": "Interface separation distance in Angstroms. Typical: 2.0-3.0 Å",
                        "default": 2.5,
                    },
                    "max_area": {
                        "type": "number",
                        "description": "Maximum interface area in Angstroms². Larger values allow more lattice mismatch",
                        "default": 300,
                    },
                },
                "required": ["film_poscar", "substrate_poscar"],
            },
        },
    },
    #SLURM Tools
    {
        "type": "function",
        "function": {
            "name": "submit_slurm_job",
            "description": "Submit a job to the Slurm cluster.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Script to run on the Slurm cluster",
                    },
                },
                "required": ["script"],
            },
        },
    },
]
