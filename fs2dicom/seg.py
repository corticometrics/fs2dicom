from fs2dicom import utils


def get_resample_aseg_cmd(aseg_image_file,
                          t1_dicom_file,
                          resampled_aseg):
    command_template = '''\
mri_vol2vol \
--mov {aseg_image_file} \
--targ {t1_dicom_file} \
--regheader \
--nearest \
--o {resampled_aseg}'''

    return command_template.format(aseg_image_file=aseg_image_file,
                                   t1_dicom_file=t1_dicom_file,
                                   resampled_aseg=resampled_aseg)


def get_generate_dicom_seg_cmd(resampled_aseg,
                               aseg_dicom_seg_metadata,
                               t1_dicom_file,
                               aseg_dicom_seg_output):
    command_template = '''\
itkimage2segimage \
--inputDICOMDirectory {t1_dicom_dir} \
--inputMetadata {aseg_dicom_seg_metadata} \
--inputImageList {resampled_aseg} \
--outputDICOM {aseg_dicom_seg_output} \
--skip'''

    t1_dicom_dir = utils.abs_dirname(t1_dicom_file)

    return command_template.format(resampled_aseg=resampled_aseg,
                                   aseg_dicom_seg_metadata=aseg_dicom_seg_metadata,
                                   t1_dicom_dir=t1_dicom_dir,
                                   aseg_dicom_seg_output=aseg_dicom_seg_output)
