import os

import aws_cdk as cdk

from wafr_genai_accelerator.wafr_genai_accelerator_stack import WafrGenaiAcceleratorStack

app = cdk.App()

# Define tags as a dictionary
tags = {
    "Project": "WellArchitectedReview"
}

# Flags for optional features
optional_features = {
    "guardrails": "True",
}

WafrGenaiAcceleratorStack(
    app,
    "WellArchitectedReviewUsingGenAIStack",
    tags=tags,
    optional_features=optional_features,
    env=cdk.Environment(account="207567766326", region="ap-south-1")
)

app.synth()
