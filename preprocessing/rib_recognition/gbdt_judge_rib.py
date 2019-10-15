"""
@Author: Leaves
@Time: 17/01/2019
@File: gbdt_judge_rib.py
@Function: train and save GBDT model
"""

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn import metrics
from sklearn.model_selection import train_test_split
from sklearn.externals import joblib
import warnings

warnings.filterwarnings("ignore")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Search some files')

    parser.add_argument('--dataset_path', required=True, dest='dataset_path', action='store', help='dataset_path')
    parser.add_argument('--saved_gbdt_path', required=True, dest='saved_gbdt_path', action='store', help='saved_gbdt_path')
    parser.add_argument('--saved_feature_path', required=True, dest='saved_feature_path', action='store', help='saved_feature_path')
    args = parser.parse_args()

    bone_data = pd.read_csv(args.dataset_path)
    # print(bone_data.columns)
    features_list = ['x_min/x_shape', 'x_max/x_shape', 'x_centroid/x_shape', 'y_min/y_shape', 'y_max/y_shape',
                     'y_centroid/y_shape', 'z_min/z_shape', 'z_max/z_shape', 'z_centroid/z_shape', 'point_count',
                     'std_z_distance_on_xoy', 'mean_z_distance_on_xoy', 'std_z_distance_div_mean_z_distance',
                     'std_x_distance_on_zoy', 'mean_x_distance_on_zoy', 'std_x_distance_div_mean_x_distance',
                     'std_y_distance_on_zox', 'mean_y_distance_on_zox', 'std_y_distance_div_mean_y_distance',
                     'iou_on_xoy', 'distance_nearest_centroid',
                     'z_length/z_shape', 'x_length/x_shape', 'y_length/y_shape']

    x = bone_data[features_list]
    y = bone_data[['target']]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=1, stratify=y)

    gbdt = GradientBoostingClassifier(random_state=3, subsample=0.7, min_samples_leaf=5)
    gbdt.fit(x_train, y_train)

    # sava gbdt model and feature list
    joblib.dump(gbdt, args.saved_gbdt_path)
    joblib.dump(features_list, args.saved_feature_path)

    y_pred = gbdt.predict(x_test)
    x_test['new_target'] = gbdt.predict(x_test)
    # print(type(x_test),type(y_pred))
    # print(x_test, y_pred)
    print("accuracy: %.4g" % (metrics.accuracy_score(y_test, y_pred)))
    # print(features_list)
    # print(gbdt.n_features)
    print(gbdt.feature_importances_)


if __name__ == '__main__':
    main()