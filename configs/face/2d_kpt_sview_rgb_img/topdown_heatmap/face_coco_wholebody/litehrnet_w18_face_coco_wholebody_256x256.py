_base_ = ['../../../../_base_/datasets/coco_wholebody_face.py']
log_level = 'INFO'
load_from = None
resume_from = None
dist_params = dict(backend='nccl')
workflow = [('train', 1)]
checkpoint_config = dict(interval=1)
evaluation = dict(interval=1, metric=['NME'], key_indicator='NME')

optimizer = dict(
    type='Adam',
    lr=2e-3,
)
optimizer_config = dict(grad_clip=None)
# learning policy
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=500,
    warmup_ratio=0.001,
    step=[40, 55])
total_epochs = 60
log_config = dict(
    interval=5,
    hooks=[
        dict(type='TextLoggerHook'),
        # dict(type='TensorboardLoggerHook')
    ])

channel_cfg = dict(
    num_output_channels=68,
    dataset_joints=68,
    dataset_channel=[
        list(range(68)),
    ],
    inference_channel=list(range(68)))

# model settings
model = dict(
    type='TopDown',
    pretrained=None,
    backbone=dict(
        type='LiteHRNet',
        in_channels=3,
        extra=dict(
            stem=dict(stem_channels=32, out_channels=32, expand_ratio=1),
            num_stages=3,
            stages_spec=dict(
                num_modules=(2, 4, 2),
                num_branches=(2, 3, 4),
                num_blocks=(2, 2, 2),
                module_type=('LITE', 'LITE', 'LITE'),
                with_fuse=(True, True, True),
                reduce_ratios=(8, 8, 8),
                num_channels=(
                    (40, 80),
                    (40, 80, 160),
                    (40, 80, 160, 320),
                )),
            with_head=True,
        )),
    keypoint_head=dict(
        type='TopdownHeatmapSimpleHead',
        in_channels=40,
        out_channels=channel_cfg['num_output_channels'],
        num_deconv_layers=0,
        extra=dict(final_conv_kernel=1, ),
        loss_keypoint=dict(type='JointsMSELoss', use_target_weight=True)),
    train_cfg=dict(),
    test_cfg=dict(
        flip_test=True,
        post_process='default',
        shift_heatmap=True,
        modulate_kernel=11))

data_cfg = dict(
    image_size=[256, 256],
    heatmap_size=[64, 64],
    num_output_channels=channel_cfg['num_output_channels'],
    num_joints=channel_cfg['dataset_joints'],
    dataset_channel=channel_cfg['dataset_channel'],
    inference_channel=channel_cfg['inference_channel'])

train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='TopDownRandomFlip', flip_prob=0.5),
    dict(
        type='TopDownGetRandomScaleRotation', rot_factor=30,
        scale_factor=0.25),
    dict(type='TopDownAffine'),
    dict(type='ToTensor'),
    dict(
        type='NormalizeTensor',
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]),
    dict(type='TopDownGenerateTarget', sigma=2),
    dict(
        type='Collect',
        keys=['img', 'target', 'target_weight'],
        meta_keys=[
            'image_file', 'joints_3d', 'joints_3d_visible', 'center', 'scale',
            'rotation', 'flip_pairs'
        ]),
]

val_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='TopDownAffine'),
    dict(type='ToTensor'),
    dict(
        type='NormalizeTensor',
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]),
    dict(
        type='Collect',
        keys=['img'],
        meta_keys=['image_file', 'center', 'scale', 'rotation', 'flip_pairs']),
]

test_pipeline = val_pipeline

data_root = 'data/coco'
data = dict(
    samples_per_gpu=32,
    workers_per_gpu=2,
    val_dataloader=dict(samples_per_gpu=32),
    test_dataloader=dict(samples_per_gpu=32),
    train=dict(
        type='FaceCocoWholeBodyDataset',
        ann_file=f'{data_root}/annotations/coco_wholebody_train_v1.0.json',
        img_prefix=f'{data_root}/train2017/',
        data_cfg=data_cfg,
        pipeline=train_pipeline,
        dataset_info={{_base_.dataset_info}}),
    val=dict(
        type='FaceCocoWholeBodyDataset',
        ann_file=f'{data_root}/annotations/coco_wholebody_val_v1.0.json',
        img_prefix=f'{data_root}/val2017/',
        data_cfg=data_cfg,
        pipeline=val_pipeline,
        dataset_info={{_base_.dataset_info}}),
    test=dict(
        type='FaceCocoWholeBodyDataset',
        ann_file=f'{data_root}/annotations/coco_wholebody_val_v1.0.json',
        img_prefix=f'{data_root}/val2017/',
        data_cfg=data_cfg,
        pipeline=val_pipeline,
        dataset_info={{_base_.dataset_info}}),
)