```
mkdir -p /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example
cd /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example
aws s3 sync s3://cmet-scratch/example_dicoms/dicoms/m28/ ./dicoms
```

Run recon-all on the source DICOMs
```
docker run -it --rm \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/fs-subs:/subjects \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/dicoms:/dicoms \
  -e FS_KEY=cGF1bEBjb3J0aWNvbWV0cmljcy5jb20KMzA0NDQKICpDZ3lrR3o2bnNYaGcKIEZTVXQweHY5UmlGcWMK \
  corticometrics/fs6-base \
    recon-all -all -i /dicoms/MR.1.3.12.2.1107.5.2.0.45074.2016081016110572496100229 -s m28
```

Rotate aseg.mgz so that it is in alignment with the source dicoms
```
docker run -it --rm \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/fs-subs:/subjects \
  -e FS_KEY=cGF1bEBjb3J0aWNvbWV0cmljcy5jb20KMzA0NDQKICpDZ3lrR3o2bnNYaGcKIEZTVXQweHY5UmlGcWMK \
  corticometrics/fs6-base \
    mri_convert --reslice_like /subjects/m28/mri/orig/001.mgz \
      -rt nearest -odt int \
      /subjects/m28/mri/aseg.mgz /subjects/m28/test.nii.gz
```

Generate DICOM-seg
```
docker run \
  -v /home/paul/cmet/git/fs2dicom/:/tmp/dcmqi \
  qiicr/dcmqi \
  itkimage2segimage \
    --inputDICOMDirectory /tmp/dcmqi/fs2dicom-rsna2018-example/dicoms \
    --inputMetadata /tmp/dcmqi/fs-aseg.json \
    --inputImageList /tmp/dcmqi/fs2dicom-rsna2018-example/fs-subs/m28/aseg-dcm.nii.gz \
    --outputDICOM /tmp/dcmqi/fs2dicom-rsna2018-example/fs-subs/m28/aseg.dcm \
    --skip
```

update segids.txt
```
python ./gen-segids-file.py ./fs-aseg.json > segids.txt
```

Convert aseg.stats into a more parseable form
```
docker run -it --rm \
  -v /home/paul/cmet/git/fs2dicom/:/work \
  -e FS_KEY=cGF1bEBjb3J0aWNvbWV0cmljcy5jb20KMzA0NDQKICpDZ3lrR3o2bnNYaGcKIEZTVXQweHY5UmlGcWMK \
  corticometrics/fs6-base \
    asegstats2table \
      --segids-from-file /work/segids.txt \
      --inputs /work/fs2dicom-rsna2018-example/fs-subs/m28/stats/aseg.stats \
      --delimiter comma --transpose --no-vol-extras \
      -t /work/fs2dicom-rsna2018-example/fs-subs/m28/aseg-stats.csv
```

Generate json for creating DICOM-SR
```
python gen-aseg-to-dicom-sr-json.py \
  ./fs2dicom-rsna2018-example/dicoms/MR.1.3.12.2.1107.5.2.0.45074.201608101611415855602883 \
  ./fs2dicom-rsna2018-example/fs-subs/m28/aseg.dcm \
  ./fs2dicom-rsna2018-example/fs-subs/m28/aseg-stats.csv \
  ./sr-tid1500-fs-example.json \
  ./fs2dicom-rsna2018-example/fs-subs/m28/aseg-stats-to-dicom-sr.json
```

Generate DICOM-SR
```
docker run \
  -v /home/paul/cmet/git/fs2dicom/:/work \
  qiicr/dcmqi \
  tid1500writer \
    --inputImageLibraryDirectory /work/fs2dicom-rsna2018-example/dicoms \
    --inputCompositeContextDirectory /work/fs2dicom-rsna2018-example/fs-subs/m28 \
    --outputDICOM /work/fs2dicom-rsna2018-example/fs-subs/m28/output-dicom-sr.dcm \
    --inputMetadata /work/fs-aseg-sr-template.json
```

Generate DICOM-SR with norm stats
```
docker run \
  -v /home/paul/cmet/git/fs2dicom/:/work \
  qiicr/dcmqi \
  tid1500writer \
    --inputImageLibraryDirectory /work/fs2dicom-rsna2018-example/dicoms \
    --inputCompositeContextDirectory /work/fs2dicom-rsna2018-example/fs-subs/m28 \
    --outputDICOM /work/fs2dicom-rsna2018-example/fs-subs/m28/output-dicom-sr.dcm \
    --inputMetadata /work/fs-aseg-sr-template-with-normstats.json
```

Interative
```
docker run \
  -it --rm \
  --entrypoint /bin/bash \
  -v /home/paul/cmet/git/fs2dicom/:/tmp/dcmqi \
  qiicr/dcmqi
```



-------------------------------------------------------------------

```
docker run -it --rm \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/fs-subs:/subjects \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/dicoms:/dicoms \
  -e FS_KEY=cGF1bEBjb3J0aWNvbWV0cmljcy5jb20KMzA0NDQKICpDZ3lrR3o2bnNYaGcKIEZTVXQweHY5UmlGcWMK \
  corticometrics/fs6-base /bin/bash
```
-------------------------------------------------------------------

### Outstanding issues:

- how to encode left/right?
  -  should 'MeasurementGroup' have something like SegmentedPropertyTypeModifierCodeSequence
  -  see schema https://raw.githubusercontent.com/qiicr/dcmqi/master/doc/schemas/sr-tid1500-schema.json
- fs-aseg.json
  - find better encodings for
    - non-WM-hypointensities (labels 80, 81, 82)
    - CC (labels 251-255)
      - see: http://dicom.nema.org/medical/Dicom/2017e/output/chtml/part16/sect_CID_2.html
- how to encode norm stats?
  - attempt in `fs-aseg-sr-template-with-normstats.json`
  - see discussion [here](https://github.com/QIICR/dcmqi/issues/305)
- make wrapper for fs
- fs data for ex? 
  - s3://cmet-scratch/dcmqi-test-dataset/

- (0020, 000E) from T1 dicom: SourceSeriesForImageSegmentation? 
- (0008, 0018) from aseg.dcm: segmentationSOPInstanceUID?

- Get rid of FreeSurfer? Use nibabel to resample (requires `nibabel` and `scipy` packages, needs the `rawavg.mgz`/`001.mgz` as input)
```
import nibabel as nb
from nibabel import processing

orig = nb.load('fs-subs/m28/mri/orig/001.mgz')
aseg = nb.load('fs-subs/m28/mri/aseg.mgz')
resampled_aseg = processing.resample_from_to(aseg, orig, mode='nearest')

nb.save(resampled_aseg, 'aseg_native_space.nii.gz')
```