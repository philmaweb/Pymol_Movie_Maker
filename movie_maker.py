'''
LICENSE

Copyright (c) 2017 Philipp Weber

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''
from pymol import cmd
import argparse  # library for parsing commandline parameters
from sys import argv
import os
from string import ascii_uppercase
# methods are only available over cmd.do when not importing polar_pairs
#   , this makes passing of variables complicated
#   we rely on the correct setting of the PYTHONPATH environment variable,
#   to include the directory in which polar_pairs.py resides
from polar_pairs import polarpairs, polartuples


#PATH TO CURRENT DIRECTORY
MOVIE_MAKER_PATH = os.environ.get('MOVIEMAKERPATH')
POLAR_INTERACTIONS_FILENAME = os.environ.get('POLAR_INTERACTION_FILENAME')
MOVIE_SCRIPT_FILENAME = os.environ.get('MOVIE_SCRIPT_FILENAME')
SESSION_NAME = "basic_movie.pse"

cmd.reinitialize()

# movie_fade available at https://raw.githubusercontent.com/Pymol-Scripts/Pymol-script-repo/master/movie_fade.py
cmd.do("run %sfade_movie.py"% (MOVIE_MAKER_PATH, ))
# define polarpairs function for usage in commandline, retrieved and extended from https://pymolwiki.org/index.php/Polarpairs
cmd.do("run %spolar_pairs.py"% (MOVIE_MAKER_PATH, ))

valid_amino_acid_3letter_codes = set("ALA CYS ASP GLU PHE GLY HIS ILE LYS LEU MET ASN PRO GLN ARG SER THR VAL TRP TYR WAT SUL HEM".split(" "))

def parse_commandline_options():

    # passed filename is first passed argument, but flags are also in argv
    print("python file loaded")
    for i, ele in enumerate(argv):
        print("argv[%s]" % i, ele)

    parser = argparse.ArgumentParser(description="Trying to parse some named parameters from shellscript")
    # parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-i", "--input", required=True)
    # parser.add_argument("--ligand_name", required=True)
    parser.add_argument("--ligand_name", type=str)
    parser.add_argument("--chain_name", type=str, default="A")
    parser.add_argument("--color_blind_friendly", default=True)
    parser.add_argument("--binding_site_radius", type=float, default=4.0)
    parser.add_argument("--check_halogen_interaction", default=False)
    parser.add_argument("--water_in_binding_site", default=True)
    parser.add_argument("--color_carbon", type=str, default="yellow")
    parser.add_argument("--session_export_version", type=float, default=1.2)
    parser.add_argument("--color_polar_interactions", type=str, default="blue")
    parser.add_argument("--cofactor_name", type=str, default="")
    parser.add_argument("--color_carbon_cofactor", type=str, default="orange")
    # parser.add_argument("--", required=True)
    args = parser.parse_args()
    options = vars(args)  # put variables into dictionary
    if args.input:
        if os.path.exists(args.input):
            input = args.input
            # Parse commandline arguments
            PDB_NAME = input.split(".")[0]
            PDB_FILENAME = PDB_NAME + ".pdb"

    # option for super basic mode
    if not args.ligand_name:
        options["no_ligand_selected"] = True

    if args.color_blind_friendly:
        if args.color_blind_friendly == "No":
            options["color_blind_friendly"] = False
        else:
            options["color_blind_friendly"] = True

    if args.check_halogen_interaction:
        if args.check_halogen_interaction == "No":
            options["check_halogen_interaction"] = False
        else:
            options["check_halogen_interaction"] = True

    if args.water_in_binding_site:
        if args.water_in_binding_site == "No":
            options["water_in_binding_site"] = False
        else:
            options["water_in_binding_site"] = True

    if args.color_carbon:
        # options are yellow, grey and orange, only need to change when color blind friendly
        if options['color_blind_friendly']:
            if args.color_carbon == "yellow":
                options["color_carbon"] = "cb_yellow"
            elif args.color_carbon == "orange":
                options["color_carbon"] = "cb_orange"

    allowed_polar_colors = set(["red", "blue", "yellow", "black", "hotpink"])
    if args.color_polar_interactions and (args.color_polar_interactions in allowed_polar_colors):
        # options are yellow, red, blue, black and hotpink
        if options['color_blind_friendly']:
            if args.color_polar_interactions != "hotpink":
                options["color_polar_interactions"] = "cb_%s" % args.color_polar_interactions
            else:
                options["color_polar_interactions"] = "hot_pink"
    else:
        if options['color_blind_friendly']:
            options["color_polar_interactions"] = "cb_blue"
        else:
            options["color_polar_interactions"] = "blue"

    session_version = 1.2
    if args.session_export_version:
        allowed_versions = {1.2, 1.72, 1.76, 1.84}
        if args.session_export_version in allowed_versions:
            session_version = args.session_export_version
    # set session_export to be of desired version
    cmd.set("pse_export_version", session_version)

    # --cofactor_name ${12} - -color_carbon_cofactor
    if args.cofactor_name:
        options['cofactor_in_binding_site'] = True
        options['cofactor_name'] = args.cofactor_name
        options['color_carbon_cofactor'] = args.color_carbon_cofactor
    else:
        options['cofactor_in_binding_site'] = False

    # load pdb file (first argument)
    # renaming the *.dat file to *.pdb, loading with pymol and renaming for galaxy
    os.rename(input, PDB_FILENAME)
    cmd.load(PDB_FILENAME)
    os.rename(PDB_FILENAME, input) # rename back to *.dat

    return options


def apply_color_switch(commandline_options):
    color_dict = {}
    color_blind_save_selected = commandline_options["color_blind_friendly"]
    cofactor_selected = commandline_options['cofactor_in_binding_site']
    if cofactor_selected:
        cofactor_color = commandline_options['color_carbon_cofactor']

    # import color settings
    cmd.do("run %scolorblindfriendly.py" % MOVIE_MAKER_PATH)
    # hotpink rgb: 255, 105, 180
    cmd.set_color("hot_pink", (255.0/255.0, 105.0/255.0, 180.0/255.0))

    if color_blind_save_selected:
        color_dict['protein_surface'] = "cb_sky_blue"
        color_dict['protein_cartoon'] = "cb_blue"
        if cofactor_selected:
            if cofactor_color in ["orange", "yellow"]:
                # color_dict['cofactor'] = "cb_%s" % cofactor_color
                color_dict['color_cofactor'] = "cb_%s" % cofactor_color
                # commandline_options['color_cofactor'] = "cb_%s" % cofactor_color
            else:
                # color_dict['cofactor'] = "grey50"
                color_dict['color_cofactor'] = "grey50"
        color_dict['binding_site'] = "grey50"
        # color_dict['interaction_polar'] = "cb_blue"
        color_dict['oxygen'] = "cb_red"
        color_dict['nitrogen'] = "cb_blue"

    else:
        color_dict['protein_surface'] = "lightblue"
        color_dict['protein_cartoon'] = "skyblue"
        if cofactor_selected:
            # color_dict['cofactor'] = cofactor_color
            color_dict['color_cofactor'] = cofactor_color
            # commandline_options['color_cofactor'] = cofactor_color
        color_dict['binding_site'] = "grey50"
        # color_dict['interaction_polar'] = "blue"
        color_dict['oxygen'] = "red"
        color_dict['nitrogen'] = "blue"

    color_dict['interaction_polar'] = commandline_options['color_polar_interactions']

    return color_dict


def apply_settings(cmd_options):
    
    settings_dict = cmd_options.copy()
    # BG Color is white
    cmd.bg_color('white')
    
    # Colors
    color_dict = apply_color_switch(cmd_options)
    color_dict["color_carbon"] = cmd_options["color_carbon"]

    settings_dict["colors"] = color_dict
    settings_dict["cartoon_transparency"] = 0.6

    settings_dict["chain_name"] = cmd_options['chain_name']
    settings_dict["ligand_name"] = cmd_options['ligand_name']
    settings_dict["binding_site_radius"] = cmd_options['binding_site_radius']
    return settings_dict


def create_selections(options):

    # Hide everything
    cmd.hide("lines")
    cmd.hide("nonbonded")

    # Protein structure
    cmd.select("protein_structure", "all")

    if options.has_key('no_ligand_selected'):
        # Super basic option, call ligand and chain from organic
        print("Attempting to automatically find ligand")
        ligand_candidates_number = cmd.select("ligand_candidate", "organic")
        candidate_resn = ""
        candidate_chain = ""
        if ligand_candidates_number:
            ligand_candidates_model = cmd.get_model("ligand_candidate")
            for cand_atom in ligand_candidates_model.atom:
                candidate_resn, candidate_chain = cand_atom.resn, cand_atom.chain
                break;
        if candidate_resn and candidate_chain:
            print("Automatically detected ligand is '%s' in chain '%s'" % (candidate_resn, candidate_chain))
            options['ligand_name'] = candidate_resn
            options['chain_name'] = candidate_chain
        else:
            raise argparse.ArgumentError("Could not automatically detect ligand. Please make sure a ligand is contained in the provided pdb-file or use the 'Basic Mode'.")

    # Ligand
    cmd.select("sele_all_ligands", "organic and chain %s and resn %s" % (options['chain_name'], options["ligand_name"]))
    number_of_ligands_selected = cmd.select("sele_ligand", 'organic and chain %s and resn %s and alt a+""' % (options['chain_name'], options["ligand_name"]))
    # remove all duplicate conformations
    cmd.remove("sele_all_ligands and not sele_ligand")
    cmd.delete("sele_all_ligands")

    #Feature: If we did not get a correct chain name from the user, we will try to guess through the whole alphabet to find it
    # otherwise the ligand will not appear in the visualization
    if not number_of_ligands_selected:
        #list holding all ascii-letters
        for letter in ascii_uppercase:
            number_of_ligands_selected = cmd.select("sele_ligand", 'organic and chain %s and resn %s and alt a+""' % (letter, options["ligand_name"]))
            if number_of_ligands_selected:
                options['chain_name'] = letter
                break

    cmd.create("ligand", "sele_ligand")
    cmd.delete("sele_ligand")
    cmd.show("sticks", "ligand")
    cmd.color(options["colors"]['color_carbon'], "ligand and e. C")
    cmd.color(options["colors"]['oxygen'], "ligand and e. O")
    cmd.color(options["colors"]['nitrogen'], "ligand and e. N")

    # Cofactor
    if options["cofactor_in_binding_site"]:
        cmd.select("sele_cofactor", "resn %s and chain %s" % (options['cofactor_name'], options['chain_name']))
        cmd.create("cofactor", "sele_cofactor")
        cmd.show("sticks", "cofactor")
        cmd.color(options['colors']['color_cofactor'], "cofactor and e. C")
        cmd.delete("sele_cofactor")

    # Surface
    cmd.create("protein_surface", "all")
    cmd.hide("lines", "protein_surface")
    cmd.hide("sticks", "protein_surface")
    cmd.hide("nonbonded", "protein_surface")
    cmd.show("surface", "protein_surface")
    cmd.color(options["colors"]['protein_surface'], "protein_surface")

    # Cartoon
    cmd.copy("protein_cartoon", "protein_surface")
    cmd.hide("surface", "protein_cartoon")
    cmd.show("cartoon", "protein_cartoon")
    cmd.color(options["colors"]['protein_cartoon'], "protein_cartoon")

    # Transparent Cartoon
    cmd.copy("protein_cartoon_transparent", "protein_cartoon")
    cmd.set("cartoon_transparency", options['cartoon_transparency'], "protein_cartoon_transparent")

    # 2nd Transparent Cartoon
    cmd.copy("protein_cartoon_transparent_more", "protein_cartoon")
    cmd.set("cartoon_transparency", 0.9, "protein_cartoon_transparent_more")

    # Binding Site
    cmd.select("sele_binding_site", "ligand expand %s"%(options['binding_site_radius']))
    cmd.select("sele_binding_site", "br. sele_binding_site")
    cmd.select("sele_binding_site", "sele_binding_site and protein_structure")
    cmd.select("sele_binding_site", "sele_binding_site and not ligand")
    cmd.create("binding_site", "sele_binding_site")
    cmd.delete("sele_binding_site")
    cmd.delete("protein_structure")
    cmd.hide("surface", "binding_site")
    cmd.hide("nonbonded")
    cmd.show("sticks", "binding_site")
    cmd.show("nb_spheres", "binding_site and not resn HOH")
    cmd.color(options["colors"]['binding_site'], "binding_site and e. C")
    cmd.color(options["colors"]['nitrogen'], "binding_site and e. N")
    cmd.color(options["colors"]['oxygen'], "binding_site and e. O")

    # get polar interacting residues in binding site without water
    cmd.select("sele_no_water_binding_site", "binding_site and not resn hoh")
    cmd.select("sele_no_water_binding_site", "sele_no_water_binding_site and not resn %s" % options['ligand_name'])
    pairs = polarpairs("sele_no_water_binding_site", "ligand", cutoff=options['binding_site_radius'], name="polar_int_d")
    if pairs:
        cmd.hide("labels", "polar_int_d")
        cmd.color(options['colors']["interaction_polar"], "polar_int_d")
    else:
        print("No polar interaction pairs found")
        options["no_polar_interactions_found"] = True
    cmd.delete("sele_no_water_binding_site")

    interacting_tuples = polartuples(pairs, selection_name="polar_interaction")

    #create a list with selection names of polar_interacting residues
    polar_selection_names = ["resi %s and resn %s and chain %s" % tup for tup in interacting_tuples]

    # write the residues into a custom text file,
    with open("%s" % (POLAR_INTERACTIONS_FILENAME, ), "w") as f:
        f.write("#POLAR INTERACTION PARTNERS WITH %s\n" % (options['ligand_name'],))
        f.write("RESI\tRESN\tCHAIN\n")
        for tup in interacting_tuples:
            f.write("%s\t%s\t%s\n" % tup)

    #select all polar interacting residues at once for an overview
    # cmd.select("polar_interacting_residues", "")
    for i, selection_name in enumerate(polar_selection_names):
        if i:  # if i>0 and we already have sele_polar_interacting_residues
            cmd.select("sele_polar_interacting_residues", "sele_polar_interacting_residues or %s" % selection_name)
            print("select sele_polar_interacting_residues, sele_polar_interacting_residues or %s" % selection_name)
        else:
            cmd.select("sele_polar_interacting_residues", selection_name)
            print("select sele_polar_interacting_residues, %s" % selection_name)

    if not options.has_key("no_polar_interactions_found"):
        cmd.create("polar_interacting_residues", "sele_polar_interacting_residues")
        cmd.delete("sele_polar_interacting_residues")

        cmd.show("sticks", "polar_interacting_residues")
        cmd.color("grey50", "polar_interacting_residues and e. C")
        cmd.color(options["colors"]['nitrogen'], "polar_interacting_residues and e. N")
        cmd.color(options["colors"]['oxygen'], "polar_interacting_residues and e. O")


    # create selection for HOH molecules in binding pocket and make nb_spheres
    if options['water_in_binding_site']:
        cmd.select("sele_water_binding_site", "binding_site and resn hoh")
        water_pairs = polarpairs("sele_water_binding_site", "ligand", cutoff=options['binding_site_radius'])

        # further filter polar interactions, discard water molecules that don't interact with binding site and ligand
        # water molecules in interacting tuples are already forming a hbond to ligand
        water_list = []
        water_distance_list = []
        water_polar_tuples_list = []

        if water_pairs:
            # print("water_bridge_candidates ", water_bridge_candidates)
            print("water_bridge_candidates ", water_pairs)
            # water_bridge_selection_names = ["resi %s and resn %s and chain %s and polar_interacting_residues" % tup for
            water_bridge_selection_names = ["(%s`%s)" % tup[0] for
                                            tup in water_pairs]
            for i, water_selection_name in enumerate(water_bridge_selection_names):
                print("Water bridge prediction \n")
                print("select sele_water%s, %s" % (i, water_selection_name))
                water_selection = cmd.select("sele_water%s" % i, water_selection_name)
                print("water selection has %s atoms" % water_selection)
                cmd.select("sele_water_partner%s"%i, "sele_water%s expand %s" % (i, options['binding_site_radius']))
                cmd.select("sele_water_partner%s"%i, "sele_water_partner%s and binding_site" %i)
                cmd.select("sele_water_partner%s"%i, "sele_water_partner%s and not ligand" %i)
                possible_binding_site_partners = cmd.select("sele_water_partner%s"%i, "sele_water_partner%s and (e. S or e. O or e. N)"%i)

                print("Predicted %s possible_binding_site_partners for %s" % (possible_binding_site_partners, water_selection_name))

                if possible_binding_site_partners:
                    # check if angles allow hbond
                    possible_pairs = polarpairs("sele_water_partner%s"%i, "sele_water%s" % i, name="d_water_%s" % i, cutoff=options['binding_site_radius'])
                    water_list.append("sele_water%s" % i)  # contains water molecule
                    water_distance_list.append("d_water_%s" % i)  # contains distance between water and binding site

                    # creates representation for residues interacting with water in binding site
                    water_polar_tuples_list.append(polartuples(possible_pairs, selection_name="h20_inter_%s"%i))
                    print("water_polar_tuples_list", water_polar_tuples_list)
                    cmd.delete("sele_water_partner%s"%i)

                else:
                    cmd.delete("sele_water%s" % i)

            # print("water_list", water_list)
            # print("water_distance_list", water_distance_list)
            # print("water_polar_tuples_list", water_polar_tuples_list)
            # now only show water from water list
            water_to_output_list = []

            # list of water selections to enable in the movie
            water_to_enable_list = []
            for water_index, (water_name, water_distance_name) in enumerate(zip(water_list, water_distance_list)):
                # number_of_water = cmd.select("sele_water_binding_site", "binding_site and resn hoh")
                number_of_water = cmd.select("sele_water_binding_site", water_name)
                if number_of_water:
                    cmd.create("water_%s" % water_index, "sele_water_binding_site")
                    cmd.show("nb_spheres", "water_%s" % water_index)

                    #get identifier of water for polar_interactions written to file
                    w_model = cmd.get_model("water_%s" % water_index)
                    for water_mol in w_model.atom:
                        water_to_output_list.append((water_mol.resi, water_mol.resn, water_mol.chain))
                    water_to_enable_list.append("water_%s" % water_index)
                    water_to_enable_list.append(water_distance_name)

                cmd.color(options['colors']["interaction_polar"], water_distance_name)
                cmd.hide("label", water_distance_name)
                cmd.delete(water_name)
            cmd.delete("sele_water_binding_site")

            #append water molecules to polar interactions file
            with open("%s" % (POLAR_INTERACTIONS_FILENAME,), "a+") as f:
                for tup in water_to_output_list:
                    # f.write("RESI\tRESN\tCHAIN\n")
                    f.write("%s\t%s\t%s\n" % tup)

            # residues interacting with water and
            options["water_to_enable_list"] = water_to_enable_list

    # Halogen Bond
    if options['check_halogen_interaction']:
        halogen_bond_selections = []
        halogen_interaction_partners = []
        for halogen in ["Cl", "Br", "I"]:
            number_of_halogen = cmd.select("sele_%s_interaction" % halogen, "ligand and e. %s" % halogen)
            print("We have %s %s atoms in our ligand" % (number_of_halogen, halogen))
            if number_of_halogen:

                cmd.select("sele_candidates",
                           "sele_%s_interaction expand 4.5" %halogen)
                cmd.select("sele_candidates",
                           "sele_candidates and (e. O or e. S)")
                number_of_candidates = cmd.select("sele_candidates",
                           "sele_candidates and binding_site and not ligand")

                print("We have %s potential candidates for %s bonds" % (number_of_candidates, halogen))
                if number_of_candidates:
                    # if angle ~160 and distance up to 4.5 A
                    # if angle 150-160 and distance up to 4.0 A
                    candidate_model = cmd.get_model("sele_candidates")
                    for atom in candidate_model.atom:
                        print("Candidate from model = %s %s" % (atom.resn, atom.index))

                    cmd.select("sele_halo", "ligand and e. %s" % halogen)
                    model_br = cmd.get_model("sele_halo")
                    candidate_model = cmd.get_model("sele_candidates")
                    for i, atom in enumerate(model_br.atom):
                        # print("i= %s" % i)
                        sele_halo = cmd.select("sele_halo%s" % i, "id %s and ligand" % atom.id)
                        # model_sele_halo = cmd.get_model("sele_halo%s" % i)
                        sele_halo_c = cmd.select("sele_halo%s_c" % i, "neighbor sele_halo%s" % i)
                        # print("sele_halo %s" % sele_halo, "sele_halo_c %s" % sele_halo_c)
                        for j, oxygen_or_sulfur in enumerate(candidate_model.atom):
                            cmd.select("ox_or_sulf_%s" %j, "id %s and binding_site" % oxygen_or_sulfur.id)
                            distance = cmd.distance("halogen_bond_%s_%s_%s" % (halogen, i, j), "sele_halo%s" % i, "ox_or_sulf_%s" % j)
                            angle = cmd.angle("halogen_bond_angle_%s_%s_%s" % (halogen, i, j), "sele_halo%s_c" % i , "sele_halo%s" % i, "ox_or_sulf_%s" % j)
                            print("Distance = %s, angle = %s" % (distance, angle))
                            if (distance <= 4.5 and angle >= 160.0) or (distance <= 4.0 and angle >= 150.0):
                                print("We have a halogen bond: halogen_bond_angle_%s_%s_%s" % (halogen, i, j))
                                cmd.hide("label", "halogen_bond_%s_%s_%s" % (halogen, i, j))
                                cmd.hide("label", "halogen_bond_angle_%s_%s_%s" % (halogen, i, j))
                                cmd.color("cb_yellow", "halogen_bond_%s_%s_%s" % (halogen, i, j))
                                cmd.color("cb_yellow", "halogen_bond_angle_%s_%s_%s" % (halogen, i, j))
                                #halogen_bond_selections.append("halogen_bond_%s_%s_%s" % (halogen, i, j))
                                halogen_bond_selections.append("halogen_bond_angle_%s_%s_%s" % (halogen, i, j))
                                cmd.create("halogen_interaction_partner%s"%i, "br. ox_or_sulf_%s" %j)
                                halogen_interaction_partners.append("halogen_interaction_partner%s"%i)
                            else:
                                print("No halogen bond, deleting selection!\n")
                                cmd.delete("halogen_bond_angle_%s_%s_%s" % (halogen, i, j))
                            # always delete bond, angle is enough
                            cmd.delete("halogen_bond_%s_%s_%s" % (halogen, i, j))
                            cmd.delete("ox_or_sulf_%s" %j)
                        #cleanup selections
                        cmd.delete("sele_halo%s" % i)
                        cmd.delete("sele_halo%s_c" % i)
                        cmd.delete("sele_halo%s_c" % i)
                        cmd.delete("sele_candidates")
                    cmd.delete("sele_halo")
            cmd.delete("sele_%s_interaction" % halogen)

        # check whether we found any halogen bond interactions
        # if halogen_bond_selections has more than one element, it will
        #   evaluate as true, if empty it will be false
        if halogen_bond_selections:
            options['halogen_bond_selections'] = halogen_bond_selections
            options['halogen_interaction_partners'] = halogen_interaction_partners



def main():
    #check wheter environment variables for output are set:
    if not MOVIE_MAKER_PATH:
        raise argparse.ArgumentError("environment variable MOVIE_MAKER_PATH not set, got '%s' instead. Please set MOVIE_MAKER_PATH with directory of this script." % MOVIE_MAKER_PATH)
    if not MOVIE_SCRIPT_FILENAME:
        raise argparse.ArgumentError("environment variable MOVIE_SCRIPT_FILENAME not set, got '%s' instead." % MOVIE_SCRIPT_FILENAME)
    if not POLAR_INTERACTIONS_FILENAME:
        raise argparse.ArgumentError("environment variable POLAR_INTERACTIONS_FILENAME not set, got '%s' instead." % POLAR_INTERACTIONS_FILENAME)

    # run all script components
    commandline_options = parse_commandline_options()
    settings_dict = apply_settings(commandline_options)
    create_selections(settings_dict)
    create_views(settings_dict)
    movie_script_file_path = "%smovie_maker_basic_script.pml" % MOVIE_MAKER_PATH

    #create scenes and frames for movie
    print("create scenes and frames for movie in %s:" % movie_script_file_path)
    generate_movie_script(options=settings_dict, filepath=movie_script_file_path)
    # execute a pymol script with @
    cmd.do("@%s" % movie_script_file_path)
    #Save session
    cmd.save("basic_movie.pse")


def create_views(options):

    polar_interactions_defined = not options.has_key("no_polar_interactions_found")
    water_in_binding_site = options["water_in_binding_site"] and options.has_key("water_to_enable_list")
    halogen_bonds_defined = options['check_halogen_interaction'] and options.has_key('halogen_bond_selections')
    # print ("polar_interactions_defined" , polar_interactions_defined)
    # print ("halogen_bonds_defined" , halogen_bonds_defined)

    cmd.disable("all")
    cmd.orient("protein_surface")
    cmd.zoom("protein_surface", 5)
    cmd.enable("protein_surface")
    cmd.set("transparency", 0.5)
    cmd.enable("protein_cartoon")
    cmd.view("1", action="store")
    cmd.scene("F1", action="store")


    # 2 and F2 show ligand in pocket
    cmd.disable("all")
    cmd.enable("protein_surface")
    cmd.set("transparency", 0.5)
    cmd.enable("protein_cartoon")
    cmd.enable("ligand")
    cmd.view("2", action="store")
    cmd.scene("F2", action="store")


    # 3 and F3
    cmd.disable("all")
    cmd.enable("protein_cartoon")
    cmd.enable("ligand")
    cmd.view("3", action="store")
    cmd.scene("F3", action="store")


    # 4 and F4
    cmd.disable("all")
    cmd.enable("ligand")
    cmd.view("4", action="store")
    cmd.scene("F4", action="store")

    # 5 and F5
    cmd.disable("all")
    cmd.enable("ligand")
    cmd.enable("protein_cartoon")
    if options["cofactor_in_binding_site"]:
        cmd.enable("cofactor")
    cmd.orient("ligand")
    cmd.zoom("binding_site", 5)
    cmd.view("5", action="store")
    cmd.scene("F5", action="store")

    # 6 and F6
    cmd.disable("all")
    cmd.enable("ligand")
    cmd.enable("binding_site")
    if options["cofactor_in_binding_site"]:
        cmd.enable("cofactor")
    if polar_interactions_defined:
        cmd.enable("polar_interacting_residues")
        cmd.enable("polar_int_d")
        cmd.zoom("polar_interacting_residues", 5)
        if water_in_binding_site:
            for sel in options["water_to_enable_list"]:
                cmd.enable(sel)
    else:
        cmd.zoom("binding_site", 5)
    cmd.view("6", action="store")
    cmd.scene("F6", action="store")

    # 7 and F7
    cmd.disable("all")
    cmd.enable("ligand")
    if options["cofactor_in_binding_site"]:
        cmd.enable("cofactor")
    # cmd.enable("binding_site")
    if polar_interactions_defined:
        cmd.enable("polar_interacting_residues")
        cmd.enable("polar_int_d")
        cmd.enable("interaction_polar")
        cmd.zoom("polar_int_d", 5)
        if water_in_binding_site:
            for sel in options["water_to_enable_list"]:
                cmd.enable(sel)
    else:
        cmd.zoom("ligand", 5)
    cmd.view("7", action="store")
    cmd.scene("F7", action="store")

    # 8 and F8
    if halogen_bonds_defined:
        cmd.disable("all")
        cmd.enable("ligand")
        for selection in options['halogen_bond_selections']:
            cmd.enable(selection)
        for selection2 in options['halogen_interaction_partners']:
            cmd.enable(selection2)
        cmd.zoom(options['halogen_bond_selections'][0], 5)
        cmd.view("8", action="store")
        cmd.scene("F8", action="store")

    # 9 and F9
    # zoom between polar interactions?
    """
    #possible addition: get all polar interacting amino acids and zoom into each of them
    # 10 frames per AA
    mset 1 x1440
    mview store

    # this code maps the zooming of
    # one AA and it's neighbor to 10 frames
    python
    for x in range(0,144):
      cmd.frame((10*x)+1)
      cmd.zoom( "n. CA and i. " + str(x) + "+" + str(x+1))
      cmd.mview("store")
    python end
    """


# generate movie script
def generate_movie_script(options, filepath):
    with open(filepath, "w+") as fh:
        # fh.write("viewport 2000, 2000\n")
        fh.write("viewport 500, 500\n")

    # Basic movie:
    # 900 frames for general inspection of protein with ligand
    # 100 frames zooming in on binding pocket + fadeout surface of protein -> F5
    # 200 frames inspection of ligand in binding pocket with cartoon display
    # 50 frames transition zoom to binding site -> F6
    # 200 frames turn 50 y and -100 y to inspect ligand interaction

    number_of_frames = 1450

    polar_interactions_defined = not options.has_key("no_polar_interactions_found")
    halogen_bonds_defined = options['check_halogen_interaction'] and options.has_key('halogen_bond_selections')

    if polar_interactions_defined:
        number_of_frames += 400

    if halogen_bonds_defined:
        number_of_frames += 250

    with open(filepath, "a+") as fh:
        fh.write("mset 1x%s\n" % number_of_frames)
        fh.write(
            """mview store, 1, scene=F1
movie_fade cartoon_transparency, 301, 1.0, 302, 0.0
turn y, 120
mview store, 100, power = 1.0
turn y, 120
mview store, 200, power = 1.0
mview store, 300, scene=F1
mview store, 301, scene=F2
turn x, 120
mview store, 400, power = 1.0
turn x, 120
mview store, 500, power = 1.0
mview store, 600, scene=F2
mview store, 601, scene=F3
turn y, 120
mview store, 700, power = 1.0
turn y, 120
mview store, 800, power = 1.0
mview store, 900, scene=F3
movie_fade cartoon_transparency, 901, 0.0, 990, 1.0
mview store, 1000, scene=F5
turn x, 50
mview store, 1100, power = 1.0
turn x, 50
mview store, 1150, scene=F5
mview store, 1200, scene=F6
turn y, 50
mview store, 1300, power = 1.0
turn y, -100
mview store, 1450, power = 1.0
"""
        )

    current_frame_number = 1450

    #only if polar interactions defined
    # 50 frames transition zoom to binding site with polar interactions -> F7
    # 300 frames turn 60 y and -120 y to inspect polar interactions
    if polar_interactions_defined:
        with open(filepath, "a+") as fh:
            fh.write(
            """mview store, 1500, scene=F7
turn y, 60
mview store, 1600, power = 1.0
turn y, -120
mview store, 1800, power = 1.0
mview store, 1850, scene=F7
"""
            )
        current_frame_number += 400

    #only if halogen interactions desired
    # 50 frames transition zoom to halogen interactions -> F8
    # 200 frames turn y 60, -120 y to inspect halogen interactions
    if halogen_bonds_defined:
        with open(filepath, "a+") as fh:
            fh.write("mview store, %s, scene=F8\n" % (current_frame_number +50))
            fh.write("turn y, 60\n")
            fh.write("mview store, %s, power = 1.0\n" % (current_frame_number+150))
            fh.write("turn y, -120\n")
            fh.write("mview store, %s, scene=F8\n" % (current_frame_number+250))
        current_frame_number += 250

    with open(filepath, "a+") as fh:
        fh.write("mview reinterpolate\n")


main()

