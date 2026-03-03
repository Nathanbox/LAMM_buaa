# 数据使用说明
## **1. 合并脚本介绍**
:据合并脚本，首先复制fastlivo生成的雷达点云数据（逐帧，包括位姿+单帧点云）到某个任务文件夹中，然后因为有多个数据合并，所以会有多个子文件夹。用以下命令运行脚本:
```
python3 merge_lidar_txts.py main_old
```
代码会重命名子文件夹（0-n），然后逐个子文件夹按照时间戳提取txt，按顺序合并然后放在上级文件夹中，并且删除原始的txt文件，同时按照时间戳重命名pcd文件（1-m）。随后就可以运行LAMM了


## 2. 运行与数据结构

Clone the repository and catkin_make:

```
cd ~/catkin_ws/src
git clone git@github.com:hku-mars/LAMM.git
catkin_make
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/usr/lib' >> ~/.bashrc
source ~/.bashrc
# if you are using zsh
# echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/usr/lib' >> ~/.zshrc
# source ~/.zshrc
```

`source devel/setup.bash` (**Note:** change the path for TBB in CMakeList.txt)

We provide a test data to demonstrate the file structure, which is available here: https://connecthkuhk-my.sharepoint.com/:u:/g/personal/hairuo_connect_hku_hk/EdWNkRVCcxVGmSRSk0vC8PMBBoeC9NpXaErjytJ1cQMXTQ?e=vAWa6R

The test data is composed of 2 part: The first part includes three sequences from KITTI00, which are steady point clouds without moving objects and can be used to test the map merging task; The seconde part includes a sequence in HeLiPR dataset,  which can be used to test the moving objects removal task.

To test your own data, you should prepare the file as follows, and remember to change relative path in launch file.

```
Data Structure for Map Merging
.
└── test_data
    ├── 0(point cloud file)
    │   ├──1.pcd(a scan)
    │   ├──2.pcd
    │   └── ...
    ├── 0.txt(pose of each scan: timestamp x y z x y z w)
    ├── 1
    │   ├──1.pcd
    │   ├──2.pcd
    │   └── ...
    ├── 1.txt
    ├── pose_correct
    └── truth
        ├──0.txt
        └──1.txt
Data Structure for Moving Objects Removal
.
└── test_data
    ├── pcd(point cloud file)
    │   ├──1.pcd
    │   ├──2.pcd
    │   └── ...
    ├── pose.txt(pose file)
    ├── once_saved
    └── twice_saved(where the steady point clouds are saved)
```

To run map merging example, you should change the path of `root_dir` in `rgb_multi_mapping.launch`, and run:

```
roslaunch btc_loop rgb_multi_mapping.launch
```

To see the merging results, you can change the path of `root_dir` and `load_dir` in `load_cloud.launch`, and run:

```
roslaunch btc_loop load_cloud.launch  
```

To make merging tasks more efficient, we make removal of moving objects an independent task. You can prepare your own data, change `load_dir`, `dyn_obj/save_file`, `dir_back` and `steady_save` in `load_cloud_rgb.launch`, and run: `roslaunch m_detector load_cloud_rgb.launch`

The result of steady point clouds of each scan and whole point clouds will be save in the twice_saved file. 
