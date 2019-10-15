#!/usr/bin/env bash

# 需要对after_join.csv 做出注释.
NII_LOC_PATH=./data/csv_files/nii_loc_df.csv
RIB_TYPE_LOCATION_PATH=./data/csv_files/rib_type_location.xls
RIB_DF_CACHE_DIR=./data/ribs_df_cache

# temp
OS=`uname -s`
#if [[ ${OS} == "Linux"  ]];then
#    RIB_DF_CACHE_DIR=./data/ribs_df_cache.last
#fi

JOIN_LABEL_PATH=./data/csv_files/join_label.csv

Voc2007_folder=./data/voc2007
Voc2007_Annotations_folder=${Voc2007_folder}/Annotations
Voc2007_ImageSets_folder=${Voc2007_folder}/ImageSets
Voc2007_JPEGImages_folder=${Voc2007_folder}/JPEGImages
Voc2007_darknet_labels=${Voc2007_folder}/labels

function re_mkdir_folder(){
    rm -rf $1
    mkdir -p $1
    echo "re mkdir $1"
}

re_mkdir_folder  ${Voc2007_Annotations_folder}
re_mkdir_folder  ${Voc2007_ImageSets_folder}
re_mkdir_folder  ${Voc2007_JPEGImages_folder}
re_mkdir_folder  ${Voc2007_darknet_labels}

# join all the rib, bounding box, excel_df
python3 ./preprocessing/prepare_data/join_xls_nii_rib.py  --ribs_df_cache_folder  ${RIB_DF_CACHE_DIR} \
                                                          --nii_loc_df_path  ${NII_LOC_PATH}  \
                                                          --rib_type_location_path  ${RIB_TYPE_LOCATION_PATH}  \
                                                          --data_join_label_path  ${JOIN_LABEL_PATH}


python3 ./preprocessing/prepare_data/voc2007/write_xml_and_pic_voc2007.py \
                                              --ribs_df_cache_folder  ${RIB_DF_CACHE_DIR} \
                                              --nii_loc_df_path  ${NII_LOC_PATH} \
                                              --rib_type_location_path  ${RIB_TYPE_LOCATION_PATH} \
                                              --data_join_label_path ${JOIN_LABEL_PATH} \
                                              --voc2007_Annotations_folder  ${Voc2007_Annotations_folder} \
                                              --output_independent_rib_folder  ${Voc2007_JPEGImages_folder} \
                                              --project_method  "x,y" \
                                              --output_format  ".jpg"

# separate voc2007 part from join part
# echo "######## split ribs_dataSet into independent picture and save offset shift ########"
#python3  ./preprocessing/prepare_data/voc2007/to_ribs_dataset_voc2007.py  --in_folder_path  ${RIB_DF_CACHE_DIR}  \
#                                         --output_independent_rib_folder  ${Voc2007_JPEGImages_folder}  \
#                                         --output_format  ".jpg"
#
#echo "######## generate voc2007 format: annotations ########"
#python3  ./preprocessing/prepare_data/voc2007/generate_xml_voc2007.py  \
#                                    --label_loc_type_info_path  ${JOIN_LABEL_PATH}  \
#                                    --voc2007_Annotations_folder  ${Voc2007_Annotations_folder}

echo "######## generate voc2007 format: imageSets ########"
python3  ./preprocessing/prepare_data/voc2007/write_imagesets_voc2007.py  \
                                       --voc2007_Annotations_folder  ${Voc2007_Annotations_folder}  \
                                       --voc2007_ImageSets_folder  ${Voc2007_ImageSets_folder}


# echo "######## voc_label from voc2007 to darknet format data"
python3 ./preprocessing/todarknet/voc_label.py
cat ${Voc2007_folder}/2007_train.txt ${Voc2007_folder}/2007_val.txt > ${Voc2007_folder}/train.txt

if [[ ${OS} == "Darwin"  ]];then
    sed -i 's/Users/home/g' ${Voc2007_folder}/*.txt
fi
