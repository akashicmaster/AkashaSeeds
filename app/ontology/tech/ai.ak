# Akasha ontology — namespace: ai
# atoms: 75

def "ai.core" "Foundational AI concepts and paradigms."
ln ai.core ont.ai sys:part_of
set.add name="ontology.ai" id="ai.core"

def "ai.ethics" "Risk, alignment, governance, social impact."
ln ai.ethics ont.ai sys:part_of
set.add name="ontology.ai" id="ai.ethics"

def "ai.llm" "Large language models and prompt-based interaction."
ln ai.llm ont.ai sys:part_of
set.add name="ontology.ai" id="ai.llm"

def "ai.ml" "Machine learning models, training, evaluation."
ln ai.ml ont.ai sys:part_of
set.add name="ontology.ai" id="ai.ml"

def "ai.platform" "AI platforms, SaaS, ecosystem directions."
ln ai.platform ont.ai sys:part_of
set.add name="ontology.ai" id="ai.platform"

def "ai.tooling" "Frameworks, libraries, runtimes, orchestration tools."
ln ai.tooling ont.ai sys:part_of
set.add name="ontology.ai" id="ai.tooling"

def "ai.workflow" "Pipelines, data flows, deployment, monitoring."
ln ai.workflow ont.ai sys:part_of
set.add name="ontology.ai" id="ai.workflow"

def "ai:accountability" "Clarity about who is responsible for AI outcomes."
ln ai:accountability ai.ethics sys:is_a
set.add name="ontology.ai" id="ai:accountability"

def "ai:agent" "Entity that perceives environment and acts toward goals."
ln ai:agent ai.core sys:is_a
set.add name="ontology.ai" id="ai:agent"

def "ai:agent_framework" "Toolkit for building multi-tool or multi-LLM agents."
ln ai:agent_framework ai.tooling sys:is_a
ln ai:agent_framework ai:agent @supports
set.add name="ontology.ai" id="ai:agent_framework"

def "ai:ai_pipeline" "End-to-end flow from data to deployed AI behavior."
ln ai:ai_pipeline ai.workflow sys:is_a
set.add name="ontology.ai" id="ai:ai_pipeline"

def "ai:ai_platform_saas" "Hosted AI platform providing APIs and managed services."
ln ai:ai_platform_saas ai.platform sys:is_a
set.add name="ontology.ai" id="ai:ai_platform_saas"

def "ai:ai_policy" "Rules and guidelines for AI deployment and usage."
ln ai:ai_policy ai.ethics sys:is_a
ln ai:ai_policy civ:policy_proposal @related_to
set.add name="ontology.ai" id="ai:ai_policy"

def "ai:akasha_pattern" "LLM collaborating with ontology engine to co-design systems."
ln ai:akasha_pattern ai.platform sys:is_a
ln ai:akasha_pattern ont.system @related_to
ln ai:akasha_pattern ont.philosophy @related_to
ln ai:akasha_pattern sys:architecture @related_to
set.add name="ontology.ai" id="ai:akasha_pattern"

def "ai:alignment" "Ensuring AI systems behave in line with human values and goals."
ln ai:alignment ai.ethics sys:is_a
ln ai:alignment ai:safety @supports
set.add name="ontology.ai" id="ai:alignment"

def "ai:bias" "Systematic deviation that unfairly favors or disadvantages groups."
ln ai:bias ai.ethics sys:is_a
set.add name="ontology.ai" id="ai:bias"

def "ai:context_window" "Maximum amount of text the model can attend to at once."
ln ai:context_window ai.llm sys:is_a
set.add name="ontology.ai" id="ai:context_window"

def "ai:copilot_pattern" "AI assisting humans in domain-specific workflows."
ln ai:copilot_pattern ai.platform sys:is_a
ln ai:copilot_pattern ont.business @related_to
ln ai:copilot_pattern biz:workflow @supports
set.add name="ontology.ai" id="ai:copilot_pattern"

def "ai:data_cleaning" "Removing errors, inconsistencies, and noise from data."
ln ai:data_cleaning ai.workflow sys:is_a
set.add name="ontology.ai" id="ai:data_cleaning"

def "ai:data_ingestion" "Process of collecting and loading data into the system."
ln ai:data_ingestion ai.workflow sys:is_a
set.add name="ontology.ai" id="ai:data_ingestion"

def "ai:edge_ai" "AI deployed close to data sources on edge devices."
ln ai:edge_ai ai.platform sys:is_a
set.add name="ontology.ai" id="ai:edge_ai"

def "ai:embedding" "Vector representation of discrete items in continuous space."
ln ai:embedding ai.ml sys:is_a
ln ai:embedding sys:data_warehouse @supports
set.add name="ontology.ai" id="ai:embedding"

def "ai:evaluation_metric" "Quantitative measure of model performance."
ln ai:evaluation_metric ai.ml sys:is_a
set.add name="ontology.ai" id="ai:evaluation_metric"

def "ai:experiment_tracker" "Tool for logging runs, metrics, and configurations."
ln ai:experiment_tracker ai.tooling sys:is_a
set.add name="ontology.ai" id="ai:experiment_tracker"

def "ai:fairness" "Property of treating individuals and groups equitably."
ln ai:fairness ai.ethics sys:is_a
set.add name="ontology.ai" id="ai:fairness"

def "ai:feature" "Input variable used by a model."
ln ai:feature ai.ml sys:is_a
set.add name="ontology.ai" id="ai:feature"

def "ai:feature_engineering" "Creating and transforming features for models."
ln ai:feature_engineering ai.workflow sys:is_a
ln ai:feature_engineering ai:feature @creates
set.add name="ontology.ai" id="ai:feature_engineering"

def "ai:feature_store" "System for managing and serving ML features."
ln ai:feature_store ai.tooling sys:is_a
ln ai:feature_store ai:feature @manages
set.add name="ontology.ai" id="ai:feature_store"

def "ai:feedback_loop" "Cycle where outputs and user behavior inform future updates."
ln ai:feedback_loop ai.workflow sys:is_a
ln ai:feedback_loop ai:model_monitoring @supports
set.add name="ontology.ai" id="ai:feedback_loop"

def "ai:framework" "Library or toolkit for building AI/ML systems."
ln ai:framework ai.tooling sys:is_a
set.add name="ontology.ai" id="ai:framework"

def "ai:governance" "Structures and processes for overseeing AI use."
ln ai:governance ai.ethics sys:is_a
ln ai:governance ont.public @related_to
ln ai:governance civ:accountability @supports
set.add name="ontology.ai" id="ai:governance"

def "ai:grounding" "Connecting model outputs to verifiable sources or data."
ln ai:grounding ai.llm sys:is_a
set.add name="ontology.ai" id="ai:grounding"

def "ai:hallucination" "Confident output that is not grounded in facts or data."
ln ai:hallucination ai.llm sys:is_a
ln ai:hallucination ai:grounding @contrasts_with
set.add name="ontology.ai" id="ai:hallucination"

def "ai:label" "Target value the model is trained to predict."
ln ai:label ai.ml sys:is_a
set.add name="ontology.ai" id="ai:label"

def "ai:llm" "Large language model trained on massive text corpora."
ln ai:llm ai.llm sys:is_a
set.add name="ontology.ai" id="ai:llm"

def "ai:local_ai_runtime" "AI runtime that runs on local devices without cloud dependency."
ln ai:local_ai_runtime ai.platform sys:is_a
ln ai:local_ai_runtime ont.system @related_to
set.add name="ontology.ai" id="ai:local_ai_runtime"

def "ai:loss_function" "Measure of error between predictions and targets."
ln ai:loss_function ai.ml sys:is_a
set.add name="ontology.ai" id="ai:loss_function"

def "ai:model_deployment" "Publishing models to production environments."
ln ai:model_deployment ai.workflow sys:is_a
ln ai:model_deployment sys:deployment @related_to
set.add name="ontology.ai" id="ai:model_deployment"

def "ai:model_evaluation" "Assessing performance using metrics and test data."
ln ai:model_evaluation ai.workflow sys:is_a
ln ai:model_evaluation ai:evaluation_metric @uses
set.add name="ontology.ai" id="ai:model_evaluation"

def "ai:model_monitoring" "Tracking drift, performance, and anomalies in production."
ln ai:model_monitoring ai.workflow sys:is_a
ln ai:model_monitoring sys:monitoring @related_to
set.add name="ontology.ai" id="ai:model_monitoring"

def "ai:model_registry" "Catalog of models with versions and metadata."
ln ai:model_registry ai.tooling sys:is_a
set.add name="ontology.ai" id="ai:model_registry"

def "ai:model_training" "Running optimization to fit model parameters."
ln ai:model_training ai.workflow sys:is_a
ln ai:model_training ai:loss_function @minimizes
set.add name="ontology.ai" id="ai:model_training"

def "ai:multi_llm_orchestration" "Using multiple LLMs with different strengths in one system."
ln ai:multi_llm_orchestration ai.platform sys:is_a
ln ai:multi_llm_orchestration ai:orchestrator @uses
set.add name="ontology.ai" id="ai:multi_llm_orchestration"

def "ai:neuro_symbolic" "Hybrid systems combining neural networks and symbolic reasoning."
ln ai:neuro_symbolic ai.core sys:is_a
set.add name="ontology.ai" id="ai:neuro_symbolic"

def "ai:optimizer" "Algorithm that updates model parameters to minimize loss."
ln ai:optimizer ai.ml sys:is_a
set.add name="ontology.ai" id="ai:optimizer"

def "ai:orchestrator" "System that routes tasks between LLMs, tools, and workflows."
ln ai:orchestrator ai.llm sys:is_a
ln ai:orchestrator ai.tooling @bridges
set.add name="ontology.ai" id="ai:orchestrator"

def "ai:overfitting" "Model fits training data too closely and fails to generalize."
ln ai:overfitting ai.ml sys:is_a
set.add name="ontology.ai" id="ai:overfitting"

def "ai:pipeline_orchestrator" "Tool for defining and running ML/LLM pipelines."
ln ai:pipeline_orchestrator ai.tooling sys:is_a
set.add name="ontology.ai" id="ai:pipeline_orchestrator"

def "ai:plugin_ecosystem" "Extension model where tools integrate into AI platforms."
ln ai:plugin_ecosystem ai.platform sys:is_a
set.add name="ontology.ai" id="ai:plugin_ecosystem"

def "ai:policy" "Mapping from states to actions in decision processes."
ln ai:policy ai.core sys:is_a
set.add name="ontology.ai" id="ai:policy"

def "ai:prompt" "Input text that conditions LLM behavior."
ln ai:prompt ai.llm sys:is_a
set.add name="ontology.ai" id="ai:prompt"

def "ai:reinforcement_learning" "Learning by trial-and-error with rewards."
ln ai:reinforcement_learning ai.ml sys:is_a
set.add name="ontology.ai" id="ai:reinforcement_learning"

def "ai:reward" "Signal indicating desirability of outcomes in reinforcement learning."
ln ai:reward ai.core sys:is_a
set.add name="ontology.ai" id="ai:reward"

def "ai:risk" "Potential for negative impact arising from AI behavior."
ln ai:risk ai.ethics sys:is_a
set.add name="ontology.ai" id="ai:risk"

def "ai:runtime" "Execution environment for models and pipelines."
ln ai:runtime ai.tooling sys:is_a
set.add name="ontology.ai" id="ai:runtime"

def "ai:safety" "Preventing harmful or unintended consequences from AI systems."
ln ai:safety ai.ethics sys:is_a
set.add name="ontology.ai" id="ai:safety"

def "ai:semi_supervised_learning" "Learning from a mix of labeled and unlabeled data."
ln ai:semi_supervised_learning ai.ml sys:is_a
set.add name="ontology.ai" id="ai:semi_supervised_learning"

def "ai:state_representation" "Encoding of environment or context for decision-making."
ln ai:state_representation ai.core sys:is_a
set.add name="ontology.ai" id="ai:state_representation"

def "ai:statistical_ai" "AI based on probabilistic models and statistics."
ln ai:statistical_ai ai.core sys:is_a
set.add name="ontology.ai" id="ai:statistical_ai"

def "ai:supervised_learning" "Learning from labeled examples."
ln ai:supervised_learning ai.ml sys:is_a
set.add name="ontology.ai" id="ai:supervised_learning"

def "ai:symbolic_ai" "Rule-based AI using explicit symbols and logic."
ln ai:symbolic_ai ai.core sys:is_a
set.add name="ontology.ai" id="ai:symbolic_ai"

def "ai:system_prompt" "Instruction defining role, constraints, or worldview for an LLM."
ln ai:system_prompt ai.llm sys:is_a
ln ai:system_prompt ai:prompt @specializes
set.add name="ontology.ai" id="ai:system_prompt"

def "ai:temperature" "Parameter controlling randomness of LLM outputs."
ln ai:temperature ai.llm sys:is_a
set.add name="ontology.ai" id="ai:temperature"

def "ai:test_set" "Data used to estimate final model performance."
ln ai:test_set ai.ml sys:is_a
set.add name="ontology.ai" id="ai:test_set"

def "ai:token" "Smallest unit of text used by the model."
ln ai:token ai.llm sys:is_a
set.add name="ontology.ai" id="ai:token"

def "ai:tool_call" "LLM-initiated request to external tools or APIs."
ln ai:tool_call ai.llm sys:is_a
set.add name="ontology.ai" id="ai:tool_call"

def "ai:top_k" "Sampling strategy limiting choices to top-k tokens."
ln ai:top_k ai.llm sys:is_a
set.add name="ontology.ai" id="ai:top_k"

def "ai:top_p" "Sampling strategy limiting cumulative probability mass."
ln ai:top_p ai.llm sys:is_a
set.add name="ontology.ai" id="ai:top_p"

def "ai:training_set" "Data used to fit model parameters."
ln ai:training_set ai.ml sys:is_a
set.add name="ontology.ai" id="ai:training_set"

def "ai:transfer_learning" "Reusing knowledge from one task in another."
ln ai:transfer_learning ai.ml sys:is_a
set.add name="ontology.ai" id="ai:transfer_learning"

def "ai:transparency" "Degree to which AI behavior and rationale are understandable."
ln ai:transparency ai.ethics sys:is_a
set.add name="ontology.ai" id="ai:transparency"

def "ai:underfitting" "Model is too simple to capture patterns in data."
ln ai:underfitting ai.ml sys:is_a
ln ai:underfitting ai:overfitting @contrasts_with
set.add name="ontology.ai" id="ai:underfitting"

def "ai:unsupervised_learning" "Learning patterns from unlabeled data."
ln ai:unsupervised_learning ai.ml sys:is_a
set.add name="ontology.ai" id="ai:unsupervised_learning"

def "ai:validation_set" "Data used to tune hyperparameters and detect overfitting."
ln ai:validation_set ai.ml sys:is_a
set.add name="ontology.ai" id="ai:validation_set"

def "ai:vector_database" "Database optimized for storing and searching embeddings."
ln ai:vector_database ai.tooling sys:is_a
ln ai:vector_database ai:embedding @stores
set.add name="ontology.ai" id="ai:vector_database"
