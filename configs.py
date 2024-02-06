from detectron2 import model_zoo
from detectron2.config import get_cfg
from detectron2.data.datasets import register_coco_instances
import os
import torch

from .src.helper import *

# basic args for tactful 
args = {
    "strategy":'com',      # strategy to be used for tactful
    "total_budget":150,  # Total data points available
    "budget":30,  # Budget per iteration
    "lake_size":150,  # Size of the lake dataset
    "train_size":42,  # Size of the training dataset
    "category":'Signature Block',   # Target Class
    "device":0,
    "proposal_budget":30,  # Budget for proposal generation
}
args["output_path"] = args['strategy']
args["iterations"] = int(args['total_budget']/args['proposal_budget'])  # Number of iterations (total_budget / budget)

# mapping required for inference
MAPPING = {'0': 'Date Block', '1': 'Logos', '2': 'Subject Block', '3': 'Body Block', '4': 'Circular ID', '5': 'Table', '6': 'Stamps/Seals', '7': 'Handwritten Text', '8': 'Copy-Forwarded To Block', '9': 'Address of Issuing Authority', '10': 'Signature', '11': 'Reference Block', '12': 'Signature Block', '13': 'Header Block', '14': 'Addressed To Block'}

train_path = 'model_result'    # path of the output dir
training_name = args['output_path']
model_path = os.path.join(train_path, training_name)
if (not os.path.exists(model_path)):
    create_dir(model_path)
output_dir = os.path.join(model_path, "initial_training")

# path to the query images dir
query_path = '/content/drive/MyDrive/tactful/query_data_img/' + args['category']    

selection_arg = {"class":args['category'], 'eta':1, "model_path":model_path, 'smi_function':args['strategy']}

# train a faster_rcnn model on the initial_set, add respective config file path
# model_cfg = "COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"
config_path = '/content/drive/MyDrive/tactful/faster_rcnn_pub_config.yml'

cfg = get_cfg()
# cfg.merge_from_file(model_zoo.get_config_file(model_cfg))
cfg.merge_from_file(config_path)   #merge config file of the model
cfg.DATASETS.TRAIN = ("initial_set",)
cfg.DATASETS.TEST = ('val_set')
cfg.DATALOADER.NUM_WORKERS = 4
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 15     # for the docvqa data
cfg.SOLVER.BASE_LR = 0.00025
cfg.SOLVER.WARMUP_ITERS = 1000
cfg.SOLVER.MAX_ITER = 500
cfg.SOLVER.IMS_PER_BATCH = 2
cfg.MODEL.RPN.NMS_THRESH = 0.8
cfg.MODEL.RPN.POST_NMS_TOPK_TEST: 2000
# cfg.TEST.EVAL_PERIOD = 1000
cfg.OUTPUT_DIR = output_dir
cfg.TRAINING_NAME = training_name
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR , "model_final.pth")   # path to the model saved after initial model train saved in output dir

if torch.cuda.is_available():
    torch.cuda.set_device(args['device'])

train_data_dirs = ("/content/drive/MyDrive/tactful/docvqa/train",
                   "/content/drive/MyDrive/tactful/docvqa/docvqa_train_coco.json")
lake_data_dirs = ("/content/drive/MyDrive/tactful/docvqa/lake")
val_data_dirs = ("/content/drive/MyDrive/tactful/docvqa/val",
                 "/content/drive/MyDrive/tactful/docvqa/docvqa_val_coco.json")

#clearing data if already exist
remove_dataset("initial_set")
remove_dataset("test_set")
remove_dataset("val_set")

# Registering dataset intial_set for initial training, test_set and val_set for test and validation respectively.
register_coco_instances(
    "initial_set", {}, train_data_dirs[1], train_data_dirs[0])
register_coco_instances("val_set", {}, val_data_dirs[1], val_data_dirs[0])

iteration = args['iterations']