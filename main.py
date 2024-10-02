import argparse
import os
import json
import shutil

def process_files(input_path, output_path):
    # Create the output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    ["train", "valid", "test"]
    for subdirectory in ["train", "valid", "test"]:
        # Create the subdirectory in the output directory
        os.makedirs(os.path.join(output_path, subdirectory), exist_ok=True)

        # Call the translate_annotations function
        translate_annotations(input_path, output_path, subdirectory)
    
    # Get the classes from the input directory
    classes = get_classes(input_path, ["train", "valid", "test"])

    # Write the data.yaml file
    write_data_yaml(output_path, len(classes), classes)

    # Zip the output directory
    shutil.make_archive(output_path, 'zip', output_path)

def translate_annotations(input_path, output_path, subdirectory):
    # Open the train directory and get a list of the images with a jpg extension
    train_dir = os.path.join(input_path, subdirectory)
    images = [f for f in os.listdir(train_dir) if f.endswith(".jpg")]

    # Open the train directory and the _annotations.coco.json file
    with open(os.path.join(input_path, f"{subdirectory}/_annotations.coco.json"), "r") as f:
        annotations = f.read()
    annotations_json = json.loads(annotations)

    # Loop over the images
    for image in images:
        # Copy the image to the output directory
        shutil.copy(os.path.join(input_path, f'{subdirectory}/{image}'), os.path.join(output_path, f'{subdirectory}/{image}'))

        # Find the image id 
        image_id = None
        for image_entry in annotations_json["images"]:
            if image_entry["file_name"] == image:
                image_id = image_entry["id"]
                break

        # Find the annotations for the image
        image_annotations = []
        for annotation in annotations_json["annotations"]:
            if annotation["image_id"] == image_id:
                image_annotations.append(annotation)

        # Create a new file with the following format: <class-index> <x1> <y1> <x2> <y2> ... <xn> <yn>
        with open(os.path.join(output_path, f"{subdirectory}/{image.replace('.jpg', '.txt')}"), "w") as f:
            for annotation in image_annotations:
                category_id = int(annotation["category_id"])-1
                segmentation = annotation["segmentation"][0]

                # Find the dimensions of the image
                width = None
                height = None
                for image_entry in annotations_json["images"]:
                    if image_entry["id"] == image_id:
                        width = image_entry["width"]
                        height = image_entry["height"]
                        break
                
                # Normalize the coordinates
                for i in range(0, len(segmentation), 2):
                    segmentation[i] /= width
                    segmentation[i+1] /= height

                f.write(f"{category_id} ")
                for i in range(0, len(segmentation), 2):
                    f.write(f"{segmentation[i]} {segmentation[i+1]} ")
                f.write("\n")

def get_classes(input_path, subdirectories):
    classes = set()
    for subdirectory in subdirectories:
        with open(os.path.join(input_path, f"{subdirectory}/_annotations.coco.json"), "r") as f:
            annotations = f.read()
        annotations_json = json.loads(annotations)

        for category in annotations_json["categories"]:
            classes.add(category["name"])
    
    return list(classes)


def write_data_yaml(output_path, nc, classes):
    data_yaml = f"""
path: 

train: train
val: valid
test: test

nc: {nc}
names: {classes}
    """

    with open(os.path.join(output_path, "data.yaml"), "w") as f:
        f.write(data_yaml)

def main():
    parser = argparse.ArgumentParser(description="A CLI tool to process files.")
    parser.add_argument('input_path', type=str, help="The path to the input directory")
    parser.add_argument('output_path', type=str, help="The path to the output directory")

    args = parser.parse_args()

    process_files(args.input_path, args.output_path)

if __name__ == "__main__":
    main()
