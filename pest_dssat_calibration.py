import os
import subprocess
from dpest.wheat.ceres import cul, eco
from dpest.wheat import overview, plantgro
from dpest import pst
from dpest.wheat.utils import uplantgro
from dpest.utils import *
import yaml


def load_yaml_config(cal_path):
    """Load the YAML configuration file from cal_path."""
    config_path = os.path.join(cal_path, "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found!")

    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    return config


def run_command(cmd):
    print(f"\nExecuting: {' '.join(cmd)}")
    subprocess.run(cmd, shell=True, check=True)


def main():
    # Define calibration folder
    cal_path = "./pest_cal1_1/"

    # Load configuration from YAML
    config = load_yaml_config(cal_path)

    # Extract variables
    ww2023_data = config["ww2023_data"]
    plantgro_variables = config["plantgro_variables"]
    overview_variables = config["overview_variables"]

    # Extract file paths
    file_paths = config["file_paths"]
    cul_file_path = file_paths["cul_file"]
    overview_file_path = file_paths["overview_file"]
    plantgro_file_path = file_paths["plantgro_file"]

    # Extract command-line settings
    commands = config["commands"]
    model_comand_line = commands["model_command"]
    py_comand_file = commands["py_command_file"]

    print(f"Loaded configuration:\n{config}")

    for treatment, cultivar in ww2023_data.items():
        print(f"\n~~~~~~~~~~~~~~~~~~~\nTreatment: {treatment}, Cultivar: {cultivar}\n~~~~~~~~~~~~~~~~~~~\n")

        # Create the folder to save the PEST files
        folder_name = cultivar.replace(" ", "")  # Remove spaces
        output_path = os.path.join(cal_path, folder_name)
        os.makedirs(output_path, exist_ok=True)  # Create the folder

        #############################
        # 1. Create PEST input files
        #############################

        # Create CULTIVAR parameters TPL file
        cultivar_parameters, cultivar_tpl_path = cul( cultivar = cultivar,
                                                      cul_file_path = cul_file_path,
                                                      output_path = output_path,
                                                      P = 'P1V, P1D',
                                                      P5 = 'P5',
                                                      G = 'G1, G2, G3',
                                                      PHINT = 'PHINT'
        )


        # Create OVERVIEW observations INS file
        overview_observations, overview_ins_path = overview(
            treatment = treatment,
            overview_file_path = overview_file_path,
            output_path = output_path,
            variables = overview_variables
        )


        if plantgro_variables is not None:
            # Create PlantGro observations INS file
            plantgro_observations, plantgro_ins_path = plantgro(
                plantgro_file_path = plantgro_file_path,
                treatment = treatment,
                variables = plantgro_variables,
                output_path = output_path
            )

        # Create the PST file
        if plantgro_variables is not None:
            pst(
                cultivar_parameters,
                dataframe_observations=[overview_observations, plantgro_observations],
                output_path=output_path,
                model_comand_line=model_comand_line,
                input_output_file_pairs=[
                    (cultivar_tpl_path, cul_file_path),
                    (overview_ins_path, overview_file_path),
                    (plantgro_ins_path, plantgro_file_path),
                ],
            )
        else:
            pst(
                cultivar_parameters,
                dataframe_observations=[overview_observations],
                output_path=output_path,
                model_comand_line=model_comand_line,
                input_output_file_pairs=[
                    (cultivar_tpl_path, cul_file_path),
                    (overview_ins_path, overview_file_path),
                ],
            )

        #############################
        # 2. PEST input files validation
        #############################

        # Validate the WHCER048_CUL.TPL File
        run_command(['tempchek.exe', cultivar_tpl_path])

        # Validate the Overview Instruction File (.INS)
        run_command(['inschek.exe', overview_ins_path, overview_file_path])

        if plantgro_variables is not None:
            # Use the uplantgro function to fill the incomplete simulation lines
            uplantgro(plantgro_file_path, treatment, plantgro_variables)

            # Validate the PlantGro Instruction File (.INS)
            run_command(['inschek.exe', plantgro_ins_path, plantgro_file_path])

        # Validate the PEST Control File (.PST)
        pst_file_path = os.path.normpath(os.path.join(output_path, 'PEST_CONTROL.pst'))
        run_command(['pestchek.exe', pst_file_path])

        # Insert the uplantgro line to the end of the Python command file
        with open(py_comand_file, 'r+') as file:
            lines = file.readlines()

            # Remove all lines that start with 'uplantgro('
            lines = [line for line in lines if not line.strip().startswith("uplantgro(")]

            # Remove trailing blank lines
            while lines and lines[-1].strip() == "":
                lines.pop()

            # Only add a new line if plantgro_variables is not None
            if plantgro_variables is not None:
                # Make sure the last remaining line ends with '\n'
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'

                # Add the new uplantgro line
                new_line = f"uplantgro('{plantgro_file_path}', '{treatment}', {plantgro_variables})\n"
                lines.append(new_line)

            # Overwrite the file with cleaned and updated lines
            file.seek(0)
            file.truncate()
            file.writelines(lines)

        #############################
        # 3. PST file first adjustments before getting the observation weights
        #############################

        print('\n ~~~~~~~~ PST file adjustment')
        #######################
        # update the noptmax value to 0 to run the model only once using the unoptmax function
        # Run the function
        noptmax(pst_file_path, new_value = 0)

        # Removes SPLITTHRESH/SPLITRELDIFF/SPLITACTION columns
        rmv_splitcols(pst_file_path)

        # Updates the RLAMBDA1 parameter
        rlambda1(pst_file_path, 5.0)

        # Updates the RLAMFAC parameter
        rlamfac(pst_file_path, 2.0)

        # Updates the PHIRATSUF parameter
        phiratsuf(pst_file_path, 0.3)

        # Updates the PHIREDLAM parameter
        phiredlam(pst_file_path, 0.03)

        ######################

        # Run the calibration one time
        run_command(['PEST.exe', pst_file_path])
        #
        # Get the observation weights
        pst_file_path_bal = os.path.join(output_path, 'PEST_CONTROL_bal.pst')
        run_command(['pwtadj1.exe', pst_file_path, pst_file_path_bal, '1.0'])

        #############################
        # 4. PST file second set of adjustments after getting the observation weights
        #############################

        # # Modify the new balanced PEST control file for full calibration updating the noptmax argument to 10000
        noptmax(pst_file_path_bal, new_value = 1000)

        # Removes SPLITTHRESH/SPLITRELDIFF/SPLITACTION columns
        rmv_splitcols(pst_file_path)

        ###########################
        # 5. Run the Calibration
        ###########################
        #pst_file_path_bal = './pest_cal1/ENTRY1/pest_control_bal.pst'
        run_command(['PEST.exe', pst_file_path_bal])

if __name__ == "__main__":
    main()