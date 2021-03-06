#IPYNB file also avaiable in the repository

# Welcome to Our ComputerVision - Bike Project

We're thrilled to show you how we built this fascinating tool using **PyTorch** to detect the legendary pedal-driven vehicles (aka the 
first "vehicle" most of us owned!) in both photos and videos (and **Yes, it is capable of analyzing any YouTube videos!** Just paste the URL link and hit run!)

<br>

---

In this project, we aim to explore the next-generation platform for object detection and segmentation, **Detectron2**. Built by Facebook AI team, Detectron2 has been integrated as part of PyTorch (a deep learning framework) to allow high-quality implementations of state-of-the-art object detection algorithms. More details to follow!

Enjoy coding!

### Prep & Installation

Frist, install all the dependencies

Note that we can run terminal commands by putting `!` before the command
"""

#Run Terminal Commands
!ls

#Install Detectron2 and Dependencies
!pip install torch==1.7.0+cu101 torchvision==0.8.1+cu101 -f https://download.pytorch.org/whl/torch_stable.html

# install dependencies: 
!pip install pyyaml==5.1 pycocotools>=2.0.1
import torch, torchvision
print(torch.__version__, torch.cuda.is_available())
!gcc --version

# # install detectron2: 
assert torch.__version__.startswith("1.7")
!pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu101/torch1.7/index.html

# Make sure compatible pillow version
!pip install pillow==7.2
# %reload_ext autoreload
# %autoreload

# Import detectron2 & common detectron2 utilities
import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog

# import libraries
import numpy as np
import os, json, cv2, random
from google.colab.patches import cv2_imshow

import tqdm
import time

"""# Dataset

We used Sense (https://sixgill.com/) to assist with image/data gathering and labeling process.

The custom dataset was saved in COCO data format and exported into JSON 3 files (Train/Val/Test) with annotations in each file.

Note that COCO (Common Objects in Context) is defined as a large-scale object detection, segmentation, and captioning dataset.

# Import a labeled Dataset from Github
"""

# download dataset from github
!git clone https://github.com/sriaphaw/ComputerVision_Bike_Jan2021.git

#Confirm the imported files
!ls ComputerVision_Bike_Jan2021

"""# Detectron2
Detectron2, a PyTorch-based modular object detection library, supports novel computer vision developments by offering implementations for all models in maskrcnn-benchmark.

### Register COCO dataset for detectron2

By registering the datasets, we are telling detectron2 how to obtain the COCO-format datasets which are "my_dataset_train", "my_dataset_val", and "my_dataset_test"
"""

# import COCO format datasets
from detectron2.data.datasets import register_coco_instances
register_coco_instances("my_dataset_train", {}, "/content/ComputerVision_Bike_Jan2021/train1.json", "/content/ComputerVision_Bike_Jan2021")
register_coco_instances("my_dataset_val", {}, "/content/ComputerVision_Bike_Jan2021/validation1.json", "/content/ComputerVision_Bike_Jan2021")
register_coco_instances("my_dataset_test", {}, "/content/ComputerVision_Bike_Jan2021/test1.json", "/content/ComputerVision_Bike_Jan2021")

# set meta data for validation set (we'll usue this later for testing)
test_metadata = MetadataCatalog.get("my_dataset_test")

"""# Training the detection model
#### Train being 80% of the entire bike imaging data, 10% for Validation and 10% for Test.

The code chunk below is to set an evaluator to run the validation dataset. The result is written to the storage.
"""

# Setup the evaluator
from detectron2.engine import DefaultTrainer
from detectron2.evaluation import COCOEvaluator

class MyTrainer(DefaultTrainer):
    @classmethod
    def build_evaluator(cls, cfg, dataset_name, output_folder=None):
        if output_folder is None:
            output_folder = os.path.join(cfg.OUTPUT_DIR,"inference")
        return COCOEvaluator(dataset_name, cfg, True, output_folder)

from detectron2.engine import DefaultTrainer

cfg = get_cfg() # initializing
cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml")) #specify model
cfg.DATASETS.TRAIN = ("my_dataset_train",)

cfg.DATALOADER.NUM_WORKERS = 0 #loading
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml") 
cfg.SOLVER.IMS_PER_BATCH = 2 # Image/batch/GPU
cfg.SOLVER.BASE_LR = 0.001  #learning rate
cfg.SOLVER.MAX_ITER = 300    #training iterations
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 32   #lower number for faster training
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1  #number of classes in dataset


# training output directory
os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

# EVAL_PERIOD=50 steps the whole Validation set is going to be evaluated
cfg.DATASETS.TEST = ("my_dataset_val",) # you can implement a validation loader
cfg.TEST.EVAL_PERIOD = 50
trainer = MyTrainer(cfg)


trainer.resume_or_load(resume=False)
trainer.train()

# Commented out IPython magic to ensure Python compatibility.
# Use TensorBoard to visualize the Train/Validation loss
# %load_ext tensorboard
# %tensorboard --logdir output

"""# Now it's time to put the **Trained Model** into action"""

!ls ./output/

# Initialize config
cfg = get_cfg()
# same with training (faster_rcnn)
cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml"))
# Directory to saved model weights (trained model)
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.DATASETS.TEST = ("my_dataset_test", )
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
# Threshhold to show predictions
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.9
# create predictor instance
predictor = DefaultPredictor(cfg)

# Run test on an image
test_image_path = '/content/ComputerVision_Bike_Jan2021/img/01EXMJ83543WMNSBE1AJHDVRNF.jpeg'
im = cv2.imread(test_image_path)
outputs = predictor(im)
v = Visualizer(im[:, :, ::-1],
                metadata=test_metadata, 
                scale=0.5
    )
out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
cv2_imshow(out.get_image()[:, :, ::-1])

# Count objects detected in an image
object_count = outputs["instances"].to("cpu")
print("Detected "+str(len(object_count))+" Bike(s)")

# Try another test
# from detectron2.utils.visualizer import ColorMode
test_image_path = '/content/ComputerVision_Bike_Jan2021/img/01EXMJ82V5PJA0QS4KKJT85T0E.jpeg'
im = cv2.imread(test_image_path)
outputs = predictor(im)
v = Visualizer(im[:, :, ::-1],
                metadata=test_metadata, 
                scale=0.5
    )
out = v.draw_instance_predictions(outputs["instances"].to("cpu"))
cv2_imshow(out.get_image()[:, :, ::-1])

"""### Evaluation metrics
Now, let's run the same evaluation process that was used in the previous validation step on the test dataset.
"""

from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.data import build_detection_test_loader
evaluator = COCOEvaluator("my_dataset_test", cfg, False, output_dir="./output/")
val_loader = build_detection_test_loader(cfg, "my_dataset_test")
print(inference_on_dataset(trainer.model, val_loader, evaluator))

"""# YouTube Time!
### It's time to run the object detection model on any fun online videos.
"""

# Insert YouTube video id found in the URL link
from IPython.display import YouTubeVideo, display
video = YouTubeVideo("rZKvUO0qO-o", width=500)
display(video)

# Dependency to download video and edit video
!pip install youtube-dl

# Download the video
!youtube-dl https://www.youtube.com/watch?v=rZKvUO0qO-o -f 22 -o video2.mp4

# Clip the video with specified time period for upcoming analysis
!ffmpeg -i /content/video2.mp4 -ss 00:00:4 -to 00:00:30 -c:v copy video-clip2.mp4

from detectron2.utils.video_visualizer import VideoVisualizer
from detectron2.utils.visualizer import ColorMode, Visualizer

# Extract video properties
video = cv2.VideoCapture('video-clip2.mp4')
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
frames_per_second = video.get(cv2.CAP_PROP_FPS)
num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

# Initialize video writer
video_writer = cv2.VideoWriter('out.mp4', fourcc=cv2.VideoWriter_fourcc(*"mp4v"), fps=float(frames_per_second), frameSize=(width, height), isColor=True)

# Initialize visualizer
v = VideoVisualizer(MetadataCatalog.get(cfg.DATASETS.TEST[0]), ColorMode.IMAGE)

def runOnVideo(video, maxFrames):
    """ Runs the predictor on every frame in the video (unless maxFrames is given),
    and returns the frame with the predictions drawn.
    """

    readFrames = 0
    while True:
        hasFrame, frame = video.read()
        if not hasFrame:
            break

        # Get prediction results for the frame
        outputs = predictor(frame)

        # Ensure the frame is colored
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Using the video visualizer to make prediction visual
        visualization = v.draw_instance_predictions(frame, outputs["instances"].to("cpu"))

        # Convert Matplotlib RGB format to OpenCV BGR format
        visualization = cv2.cvtColor(visualization.get_image(), cv2.COLOR_RGB2BGR)

        yield visualization

        readFrames += 1
        if readFrames > maxFrames:
            break

# Itemize the frames of the video
for visualization in tqdm.tqdm(runOnVideo(video, num_frames), total=num_frames):

    # Write to video file
    video_writer.write(visualization)

# Release the data
video.release()
video_writer.release()
cv2.destroyAllWindows()

"""# The analyzed result is here!!
### Who's excited!?
"""

# Download the video
from google.colab import files
files.download('out.mp4')
