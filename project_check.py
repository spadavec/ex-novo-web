from pypdb import *
from chembl_webresource_client.new_client import new_client
import datetime as dt
from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
import sys

app = Flask(__name__)
api = Api(app)
engine = create_engine('sqlite:///ids.db')


def search_for_pdb(accession):

    # Generate the search dictionary to be converted to XML
    search_dict = make_query('{}'.format(accession), 'UpAccessionIdQuery')

    # Perform search
    found_pdbs = do_search(search_dict)

    # Return the number of pdbs found for this particular acccession code
    return found_pdbs

@app.route('/')
def project_check():
    resolutions = []
    has_lig = []
    pdb_pass = False
    ligand_pass = False
    info = {}
    pdb_id = []
    RESOLUTION_MINIMUM = float(2.5)

    connection = engine.connect()
    chembl_query = connection.execute("select CHEMBL_ID from ids")
    accession_query = connection.execute("select ACCESSION from ids")


    chembl_ids = [x[0] for x in chembl_query.cursor.fetchall()]
    accession = [x[0] for x in accession_query.cursor.fetchall()]


    print("chembl_ids")
    print(chembl_ids)
    print("accession")
    print(accession)



    pdb_codes = search_for_pdb(accession[0])
    pdb_codes = [x.split(':')[0] for x in pdb_codes if len(x.split(':')[0]) > 3]

    activity = new_client.activity
    target = new_client.target


    print(pdb_codes)
    print(accession)
    if len(pdb_codes) > 0:
        for pdb in pdb_codes:
            # Get PDB Metadata
            info = describe_pdb(pdb)
            resolutions.append(info['resolution'])

            # Get Ligand Metadata
            ligand_dict = get_ligands('{}'.format(pdb))

            # If there are ligands, make note
            if len(ligand_dict) > 0:
                has_lig.append('True')

    for i,x in enumerate(resolutions):
        if float(x) <= RESOLUTION_MINIMUM:
            pdb_id.append(pdb_codes[i])
            pdb_pass = True
            pass
        if pdb_pass and 'True' in has_lig:
            for x in chembl_ids:
                temp = []
                print("starting hard part")
                res = activity.filter(target_chembl_id='{}'.format(x), confidence_score= 9, assay_type='B', standard_type="IC50")
                f = list(res)
                if len(res) > 400:
                    for z in f:
                        if z['parent_molecule_chembl_id'] and z['canonical_smiles'] and z['standard_value'] is not None:
                            temp.append([str(z['parent_molecule_chembl_id']), str(z['canonical_smiles']), float(z['standard_value'])])
                else:
                    ligand_pass = False
            if len(temp) >= 400:
                ligand_pass = True
            else:
                ligand_pass = False
        else:
            pdb_pass = False


    return pdb_pass, pdb_id, ligand_pass


if __name__ == '__main__':
    app.run()
