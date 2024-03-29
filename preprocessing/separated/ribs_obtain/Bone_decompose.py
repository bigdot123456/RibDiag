import numpy as np
import pandas as pd
import skimage
import matplotlib.pyplot as plt
import gc
from skimage.measure import label
from sklearn.externals import joblib
import sys, os


def add_python_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)


add_python_path(os.getcwd())
# from projects
from preprocessing.separated.ribs_obtain.Bone_Spine_Predict import BoneSpine
from preprocessing.separated.ribs_obtain.Bone_prior import BonePrior
from preprocessing.separated.ribs_obtain.Spine_Remove import SpineRemove
from preprocessing.separated.ribs_obtain.Remove_Sternum import SternumRemove
from preprocessing.separated.ribs_obtain.util import (plot_yzd, sparse_df_to_arr, arr_to_sparse_df, timer,
                                                      loop_morphology_binary_opening, source_hu_value_arr_to_binary,
                                                      arr_to_sparse_df_only, plot_binary_array)
#from preprocessing.separated.ribs_obtain.Bone_v2 import BonePredict
from preprocessing.separated.ribs_obtain.Bone_Predict import BonePredict
# load gbdt model and feature list

sys.setrecursionlimit(10000)


def judge_collect_spine_judge_connected_rib(sparse_df=None, cluster_df=None, bone_prior=None, output_prefix=None,
                                            opening_times=None, all_debug=False):
    """
    Combine all spine bone , and decide whether the combine spine connected ribs_obtain?
    :return loc_spine_connected_rib: if the remaining bone connect with ribs_obtain?
    :return remaining_bone_df: the remaining spine
    :return sternum_bone_df: the sternum
    """
    remaining_bone_df = pd.DataFrame({})
    loc_spine_connected_rib = False
    for e in cluster_df['c'].values:
        temp_sparse_df = sparse_df[sparse_df['c'] == e]
        # will add center line , @issac
        single_bone = BoneSpine(bone_data=temp_sparse_df, arr_shape=bone_prior.get_prior_shape(), spine_width=100,
                                prior_zoy_center_y_axis_line_df=bone_prior.get_zoy_symmetric_y_axis_line_df(),
                                detection_objective='spine or sternum', output_prefix=output_prefix)

        single_bone.detect_spine_and_sternum()

        # save single bone fig
        if all_debug:
            plt.figure()
            plt.title('os:%d, r:%s, p_cnt:%s, y_mx_on_z:%d' % (opening_times,
                                                               cluster_df[cluster_df['c'] == e].index[0],
                                                               len(temp_sparse_df),
                                                               single_bone.get_y_length_statistics_on_z(feature='max')
                                                               ),
                      color='red')
            single_bone.plot_bone(save=True, save_path='{}/opening_{}_label_{}_collect.png'.format(output_prefix,
                                                                                                   opening_times,
                                                                                                   e))

        if single_bone.is_spine():
            # single_bone.get_bone_data().to_csv('{}/is_spine_{}', index=False)
            remaining_bone_df = remaining_bone_df.append(single_bone.get_bone_data())
            if single_bone.spine_connected_rib():
                loc_spine_connected_rib = True

        del single_bone

    return loc_spine_connected_rib, remaining_bone_df


"""
def collect_ribs_v2(value_arr, hu_threshold=150, bone_prior=None, allow_debug=False, output_prefix=None,
                 bone_info_path=None, rib_recognition_model_path=None):
    # read models from
    GBDT = joblib.load('{}/gbdt.pkl'.format(rib_recognition_model_path))
    FEATURE_LIST = joblib.load('{}/feature.pkl'.format(rib_recognition_model_path))

    # generate binary array from source HU array for labeling
    binary_arr = value_arr.copy()
    binary_arr[binary_arr < hu_threshold] = 0
    binary_arr[binary_arr >= hu_threshold] = 1
    # bone labeling
    label_arr = skimage.measure.label(binary_arr, connectivity=2)
    del binary_arr

    with timer("########_collect arr to sparse"):
        sparse_df, cluster_df = arr_to_sparse_df(label_arr=label_arr, add_pixel=True, pixel_arr=value_arr,
                                                 sort=True, sort_key='c.count', keep_by_top=True, top_nth=40,
                                                 keep_by_threshold=True, threshold_min=5000)

    with timer("########_bone predict"):
        bone_predict = BonePredict(bone_data=sparse_df, arr_shape=bone_prior.get_prior_shape())
        features = bone_predict.get_features_for_all_bones()
        # features.to_csv('/Users/liqinghua/Desktop/chek-nan.csv')
        features['target'] = GBDT.predict(features[FEATURE_LIST])
        features.to_csv(bone_info_path, index=False, columns=FEATURE_LIST + ['target'])
        for idx, row in features.iterrows():
            class_id = row['class_id']
            target = row['target']
            save_path = '{}/label_{}_collect_{}_RIB.png'.format(output_prefix, 'IS' if target == 1 else 'NOT', class_id)
            bone_predict.plot_bone(class_id=class_id, save=True, save_path=save_path)

        is_rib_list = features[features['target'] == 1]['class_id']

    return sparse_df[sparse_df['c'].isin(is_rib_list)]
"""


def collect_ribs(value_arr, hu_threshold=150, bone_prior=None, allow_debug=False, output_prefix=None,
                 bone_info_path=None, rib_recognition_model_path=None):
    # read models from
    GBDT = joblib.load('{}/gbdt.pkl'.format(rib_recognition_model_path))
    FEATURE_LIST = joblib.load('{}/feature.pkl'.format(rib_recognition_model_path))

    # generate binary array from source HU array for labeling
    binary_arr = value_arr.copy()
    binary_arr[binary_arr < hu_threshold] = 0
    binary_arr[binary_arr >= hu_threshold] = 1
    # bone labeling
    label_arr = skimage.measure.label(binary_arr, connectivity=1)
    del binary_arr

    with timer("########_collect arr to sparse"):
        sparse_df, cluster_df = arr_to_sparse_df(label_arr=label_arr, add_pixel=True, pixel_arr=value_arr,
                                                 sort=True, sort_key='c.count', keep_by_top=True, top_nth=40,
                                                 keep_by_threshold=True, threshold_min=5000)
    del label_arr

    rib_bone_df = pd.DataFrame({})
    bone_info_df = pd.DataFrame({}, columns=FEATURE_LIST+['target', 'class_id'])

    for e in cluster_df['c'].values:
        temp_sparse_df = sparse_df[sparse_df['c'] == e]
        # will add center line , @issac
        with timer("########_only rib bone"):
            single_bone = BonePredict(bone_data=temp_sparse_df, arr_shape=bone_prior.get_prior_shape(), spine_width=100,
                                      prior_zoy_center_y_axis_line_df=bone_prior.get_zoy_symmetric_y_axis_line_df())

        with timer("########_only rib bone predict"):
            #if single_bone.is_multi_ribs():
            #    rib_bone_df = rib_bone_df.append(single_bone.get_bone_data())
            #    single_bone.plot_bone(save=True, save_path='{}/label_{}_collect_IS_MULTI_RIB.png'.format(output_prefix, e))

            temp_single_bone_feature = single_bone.get_rib_feature_for_predict()
            pre_target = GBDT.predict([[temp_single_bone_feature[i] for i in FEATURE_LIST]])
            temp_single_bone_feature['target'] = pre_target[0]
            # print(pre_target)
            if pre_target[0] > 1.5:
                single_bone.cut_multi_ribs()
                rib_bone_df = rib_bone_df.append(single_bone.get_bone_data())
                single_bone.plot_bone(save=True,
                                      save_path='{}/label_{}_collect_IS_MULT_RIB.png'.format(output_prefix, e))
                single_bone.get_bone_data().to_csv('{}/label_{}_collect_IS_MULT_RIB.csv'.format(output_prefix, e),
                                                   index=False)
            if pre_target[0] > 0.5:
                rib_bone_df = rib_bone_df.append(single_bone.get_bone_data())
                single_bone.plot_bone(save=True,
                                      save_path='{}/label_{}_collect_IS_RIB.png'.format(output_prefix, e))
            else:
                single_bone.get_bone_data().to_csv('{}/label_{}_collect_NOT_RIB.csv'.format(output_prefix, e),
                                                   index=False)
                single_bone.plot_bone(save=True, save_path='{}/label_{}_collect_NOT_RIB.png'.format(output_prefix, e))

            temp_single_bone_feature['class_id'] = e
            bone_info_df.loc[len(bone_info_df)] = temp_single_bone_feature

        del single_bone

    bone_info_df.sort_values(by='class_id', inplace=True)
    bone_info_df.to_csv(bone_info_path, index=False, columns=FEATURE_LIST+['target', 'class_id'])
    return rib_bone_df


def loop_opening_get_spine(binary_arr, bone_prior=None, output_prefix=None, allow_debug=True,
                           hyper_opening_times=1):

    # calc bone prior
    # sternum_bone_df = pd.DataFrame({})
    _opening_times = 0
    while True:
        # circulation times
        with timer('_________label'):
            label_arr = skimage.measure.label(binary_arr, connectivity=2)
        del binary_arr

        with timer('_________arr to sparse df'):
            # add select objective.
            sparse_df, cluster_df = arr_to_sparse_df(label_arr=label_arr, sort=True, sort_key='c.count',
                                                     keep_by_top=True, top_nth=10,
                                                     keep_by_threshold=True, threshold_min=4000)
        del label_arr
        with timer('_________collect spine and judge connected'):
            glb_spine_connected_rib, _remaining_bone_df = judge_collect_spine_judge_connected_rib(sparse_df=sparse_df,
                                                                                                  cluster_df=cluster_df,
                                                                                                  bone_prior=bone_prior,
                                                                                                  output_prefix=output_prefix,
                                                                                                  opening_times=_opening_times)

        if allow_debug:
            _remaining_bone_df.to_csv("{}/is_spine_opening_{}th.csv".format(output_prefix, _opening_times), index=False)
        del sparse_df, cluster_df

        if (glb_spine_connected_rib is False) or (_opening_times >= hyper_opening_times):
            break
        _opening_times = _opening_times + 1
        with timer('_________sparse df to arr'):
            binary_arr = sparse_df_to_arr(arr_expected_shape=bone_prior.get_prior_shape(),
                                          sparse_df=_remaining_bone_df, fill_bool=True)

        with timer('_________binary opening'):
            binary_arr = loop_morphology_binary_opening(binary_arr, use_cv=False, opening_times=_opening_times)

    return _remaining_bone_df


def void_cut_ribs_process(value_arr, allow_debug=False, output_prefix='hello', bone_info_path=None,
                          rib_df_cache_path=None, rib_recognition_model_path=None, hyper_opening_times=2):

    with timer('calculate basic array and feature, data frame'):
        """covert source HU array to binary array with HU threshold = 400
        """
        binary_arr = source_hu_value_arr_to_binary(value_arr=value_arr, hu_threshold=400)

        """calculate center of source CT array
        """
        # z_center = binary_arr.shape[0] // 2
        x_center = binary_arr.shape[1] // 2
        y_center = binary_arr.shape[2] // 2

    with timer('calc bone prior'):
        """calculate bone prior
        """
        bone_prior = BonePrior(binary_arr=binary_arr)

    with timer('calculate envelope of sternum and remove sternum with sternum envelope'):
        """calculate envelope of sternum
        """
        half_front_bone_df = arr_to_sparse_df_only(binary_arr=binary_arr[:, :x_center, :])

        """remove sternum
        """
        sternum_remove = SternumRemove(bone_data_arr=value_arr,
                                       bone_data_df=half_front_bone_df,
                                       bone_data_shape=value_arr.shape,
                                       center_line=y_center,
                                       hu_threshold=400, width=100,
                                       output_prefix=output_prefix)

        sternum_remove.sternum_remove_operation(value_arr=value_arr)

        """plot half front bone"""
        if allow_debug:

            plot_binary_array(binary_arr=binary_arr[:, :x_center, :], title='half_front_bone',
                              save=True, save_path=os.path.join(output_prefix, 'half_front_bone.png'),
                              line_tuple_list=[(np.arange(binary_arr.shape[0]), sternum_remove.left_envelope_line),
                                               (np.arange(binary_arr.shape[0]), sternum_remove.right_envelope_line)])

        del half_front_bone_df
        del sternum_remove
        gc.collect()

    with timer('get spine with looping opening and remove remaining spine from CT images'):
        """looping spine to get opening
        """
        remaining_bone_df = loop_opening_get_spine(binary_arr=binary_arr,
                                                   bone_prior=bone_prior,
                                                   output_prefix=output_prefix,
                                                   hyper_opening_times=hyper_opening_times)

        spine_remove = SpineRemove(bone_data_df=remaining_bone_df,
                                   bone_data_shape=bone_prior.get_prior_shape(),
                                   allow_envelope_expand=True,
                                   expand_width=20)
        spine_remove.spine_remove_operation(value_arr=value_arr)

        """plot split spine"""
        if allow_debug:
            if len(remaining_bone_df) > 0:
                _all_index_in_envelope = spine_remove.get_all_index_in_envelope()
                plot_yzd(temp_df=remaining_bone_df, shape_arr=(binary_arr.shape[0], binary_arr.shape[2]),
                         save=True, save_path='{}/spine_remaining.png'.format(output_prefix),
                         line_tuple_list=[(_all_index_in_envelope['z'], _all_index_in_envelope['y.min']),
                                          (_all_index_in_envelope['z'], _all_index_in_envelope['y.max'])])
            else:
                print("remaining_bone_df is empty!")

        del remaining_bone_df
        del spine_remove
        gc.collect()

    with timer('collect ribs_obtain'):
        """collecting ribs_obtain from value array after removing spine and sternum
        """
        rib_bone_df = collect_ribs(value_arr, hu_threshold=150, bone_prior=bone_prior, output_prefix=output_prefix,
                                   bone_info_path=bone_info_path,
                                   rib_recognition_model_path=rib_recognition_model_path)

        rib_bone_df.to_csv(rib_df_cache_path, columns=['x', 'y', 'z', 'c', 'v'], index=False)

        """plot collected ribs_obtain"""
        if allow_debug:
            restore_arr = np.zeros(bone_prior.get_prior_shape())
            if len(rib_bone_df) > 0:
                rib_index_all = rib_bone_df['z'].values, rib_bone_df['x'].values, rib_bone_df['y'].values
                restore_arr[rib_index_all] = 1

                plot_binary_array(binary_arr=restore_arr, title='collect_ribs',
                                  save=True, save_path=os.path.join(output_prefix, 'collect_ribs.png'))
            else:
                print("collect rib bone df = 0")
            del restore_arr

    del binary_arr
    del rib_bone_df
    del bone_prior
    del value_arr
    gc.collect()
