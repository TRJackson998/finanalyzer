import os
import pandas as pd
from Assets.category_mappings import category_mappings


def fill_dict(working_dict: dict[str, list[str]], in_csv: str) -> dict[str, list[str]]:
    """Reads csv, prompts user to add to dictionary if descriptions are missing their category"""
    df = pd.read_csv(in_csv)

    # get more category options from the csv's categories
    category_options = []
    for category in df["Category"].unique():
        if category not in working_dict.keys():
            category_options.append(category)
    category_options.sort()

    working_dict = sort_dict(working_dict)

    # check the mapping dict for each description in the csv
    for description in df["Description"].unique():
        found = False
        for key in working_dict.keys():
            if description in working_dict[key]:
                found = True
        # not in the mapping dict, get user input
        if not found:
            # print currrent available categories
            i = 0
            for category in working_dict.keys():
                print(f"{i}: {category}")
                i += 1
            # get input
            print(
                f"{description} not found, please input the number or name of the category it belongs to, or -1 for more options."
            )
            chosen_category = input(f"{description} belongs to category: ")

            # display further options if requested by user
            if chosen_category == "-1":
                i = 0
                for category in category_options:
                    print(f"{i}: {category}")
                    i += 1
                chosen_category = input(f"{description} belongs to category: ")
                chosen_category = category_options[int(chosen_category)]

            # try to put the description into the dict
            try:
                # first attempt assumes int input, checks in working dict keys
                keys = [key for key in working_dict]
                chosen_category = keys[int(chosen_category)]
                working_dict[chosen_category].append(description)
            except:
                # try it as a string instead, if it exists in working dict keys or extra category option list
                if (chosen_category in category_options) | (
                    chosen_category in list(working_dict.keys())
                ):
                    try:
                        # try to append to existing list at that key
                        working_dict[chosen_category].append(description)
                    except:
                        # list doesn't exist, create it
                        working_dict[chosen_category] = [description]
                else:
                    # this category isn't one of the options
                    print(f"Invalid category chosen: {chosen_category}")

                    # prompt to ask user if they want to add it
                    yes = input(f"Use {chosen_category} as new category name? (y/n): ")
                    if yes.lower() == "y":
                        working_dict[str(chosen_category)] = [description]
                    else:
                        # try again on the next run, this one's getting skipped
                        print("Error, skipping...")
    return working_dict


def sort_dict(in_dict: dict[str, list[str]]) -> dict[str, list[str]]:
    """Takes a dictionary input and returns it with the keys in alphabetical order"""
    sorted_keys = sorted(in_dict)
    out_dict = {}
    for key in sorted_keys:
        out_dict[key] = in_dict[key]
    return out_dict


def write_dict(in_dict: dict[str, list[str]], outpath: str) -> None:
    """Takes dictionary and path input, writes dictionary to file at path"""
    with open(outpath, "w") as outfile:
        in_dict = sort_dict(in_dict)

        # only take the keys that have data in them
        out_dict = {}
        for key in list(in_dict.keys()):
            if in_dict[key]:
                out_dict[key] = in_dict[key]

        # formatting
        out_dict = str(out_dict).replace("], ", "],\n    ")

        outfile.write(f"category_mappings = {out_dict}")


def generate_mappings():
    """Runtime Function"""
    working_dict = category_mappings
    assets_dir = os.path.join(".\\Analyze_Finances", "Assets")
    for file in os.scandir(assets_dir):
        if file.name.endswith(".csv"):
            working_dict = fill_dict(working_dict, os.path.join(assets_dir, file.name))
            write_dict(working_dict, os.path.join(assets_dir, "category_mappings.py"))
