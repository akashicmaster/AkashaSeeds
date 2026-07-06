# Akasha ontology — namespace: ctrl
# atoms: 34

def "ctrl.classical" "Classical control methods including PID and frequency-domain design."
ln ctrl.classical ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.classical"

def "ctrl.digital" "Digital control and discrete-time systems."
ln ctrl.digital ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.digital"

def "ctrl.identification" "System identification and modeling from data."
ln ctrl.identification ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.identification"

def "ctrl.nonlinear" "Nonlinear control methods."
ln ctrl.nonlinear ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.nonlinear"

def "ctrl.optimal" "Optimal control including LQR and MPC."
ln ctrl.optimal ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.optimal"

def "ctrl.robust" "Robust control including H-infinity and μ-synthesis."
ln ctrl.robust ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.robust"

def "ctrl.stability" "Stability analysis and Lyapunov methods."
ln ctrl.stability ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.stability"

def "ctrl.state_space" "State-space modeling and control."
ln ctrl.state_space ont.control_engineering sys:part_of
set.add name="ontology.control_engineering" id="ctrl.state_space"

def "ctrl:backstepping" "Backstepping design for cascaded nonlinear systems."
ln ctrl:backstepping ctrl.nonlinear sys:is_a
set.add name="ontology.control_engineering" id="ctrl:backstepping"

def "ctrl:bode_design" "Frequency-domain design using Bode plots."
ln ctrl:bode_design ctrl.classical sys:is_a
set.add name="ontology.control_engineering" id="ctrl:bode_design"

def "ctrl:discrete_pid" "Discrete-time PID implementation."
ln ctrl:discrete_pid ctrl.digital sys:is_a
set.add name="ontology.control_engineering" id="ctrl:discrete_pid"

def "ctrl:feedback_linearization" "Feedback linearization for nonlinear systems."
ln ctrl:feedback_linearization ctrl.nonlinear sys:is_a
ln ctrl:feedback_linearization ctrl:lyapunov_stability @analyzed_with
set.add name="ontology.control_engineering" id="ctrl:feedback_linearization"

def "ctrl:gain_phase_margin" "Gain and phase margins for robustness assessment."
ln ctrl:gain_phase_margin ctrl.stability sys:is_a
set.add name="ontology.control_engineering" id="ctrl:gain_phase_margin"

def "ctrl:grey_box_modeling" "Grey-box modeling combining physics and data."
ln ctrl:grey_box_modeling ctrl.identification sys:is_a
set.add name="ontology.control_engineering" id="ctrl:grey_box_modeling"

def "ctrl:h_infinity" "H-infinity robust control design."
ln ctrl:h_infinity ctrl.robust sys:is_a
ln ctrl:h_infinity ctrl.robust @core_method
set.add name="ontology.control_engineering" id="ctrl:h_infinity"

def "ctrl:kalman_filter" "Kalman filter for optimal state estimation."
ln ctrl:kalman_filter ctrl.state_space sys:is_a
ln ctrl:kalman_filter ctrl:lqg_control @combined_in
set.add name="ontology.control_engineering" id="ctrl:kalman_filter"

def "ctrl:lead_lag" "Lead-lag compensators for shaping frequency response."
ln ctrl:lead_lag ctrl.classical sys:is_a
set.add name="ontology.control_engineering" id="ctrl:lead_lag"

def "ctrl:lqg_control" "Linear Quadratic Gaussian control combining LQR and Kalman filter."
ln ctrl:lqg_control ctrl.optimal sys:is_a
set.add name="ontology.control_engineering" id="ctrl:lqg_control"

def "ctrl:lqr_control" "Linear Quadratic Regulator for optimal state feedback."
ln ctrl:lqr_control ctrl.optimal sys:is_a
ln ctrl:lqr_control ctrl:state_feedback @implements
set.add name="ontology.control_engineering" id="ctrl:lqr_control"

def "ctrl:lyapunov_stability" "Lyapunov-based stability analysis."
ln ctrl:lyapunov_stability ctrl.stability sys:is_a
set.add name="ontology.control_engineering" id="ctrl:lyapunov_stability"

def "ctrl:mpc" "Model Predictive Control using constrained optimization."
ln ctrl:mpc ctrl.optimal sys:is_a
ln ctrl:mpc ctrl.optimal @advanced_form_of
set.add name="ontology.control_engineering" id="ctrl:mpc"

def "ctrl:mu_synthesis" "Mu-synthesis for structured uncertainty."
ln ctrl:mu_synthesis ctrl.robust sys:is_a
set.add name="ontology.control_engineering" id="ctrl:mu_synthesis"

def "ctrl:nonparametric_identification" "Nonparametric identification using frequency response and impulse response."
ln ctrl:nonparametric_identification ctrl.identification sys:is_a
set.add name="ontology.control_engineering" id="ctrl:nonparametric_identification"

def "ctrl:nyquist_criterion" "Nyquist criterion for closed-loop stability."
ln ctrl:nyquist_criterion ctrl.stability sys:is_a
set.add name="ontology.control_engineering" id="ctrl:nyquist_criterion"

def "ctrl:parametric_identification" "Parametric system identification using models such as ARX and state-space."
ln ctrl:parametric_identification ctrl.identification sys:is_a
set.add name="ontology.control_engineering" id="ctrl:parametric_identification"

def "ctrl:pid" "PID controller combining proportional, integral, and derivative actions."
ln ctrl:pid ctrl.classical sys:is_a
ln ctrl:pid ctrl:gain_phase_margin @evaluated_by
set.add name="ontology.control_engineering" id="ctrl:pid"

def "ctrl:root_locus" "Root locus method for pole placement."
ln ctrl:root_locus ctrl.classical sys:is_a
set.add name="ontology.control_engineering" id="ctrl:root_locus"

def "ctrl:sample_and_hold" "Sampling and hold operations in digital control."
ln ctrl:sample_and_hold ctrl.digital sys:is_a
set.add name="ontology.control_engineering" id="ctrl:sample_and_hold"

def "ctrl:sensitivity_shaping" "Sensitivity function shaping for robustness."
ln ctrl:sensitivity_shaping ctrl.robust sys:is_a
set.add name="ontology.control_engineering" id="ctrl:sensitivity_shaping"

def "ctrl:sliding_mode" "Sliding mode control for robustness in nonlinear systems."
ln ctrl:sliding_mode ctrl.nonlinear sys:is_a
set.add name="ontology.control_engineering" id="ctrl:sliding_mode"

def "ctrl:state_feedback" "State feedback control using full state measurements."
ln ctrl:state_feedback ctrl.state_space sys:is_a
set.add name="ontology.control_engineering" id="ctrl:state_feedback"

def "ctrl:state_observer" "State observer estimating unmeasured states."
ln ctrl:state_observer ctrl.state_space sys:is_a
set.add name="ontology.control_engineering" id="ctrl:state_observer"

def "ctrl:state_space_model" "State-space representation of dynamic systems."
ln ctrl:state_space_model ctrl.state_space sys:is_a
set.add name="ontology.control_engineering" id="ctrl:state_space_model"

def "ctrl:z_transform" "Z-transform for discrete-time system analysis."
ln ctrl:z_transform ctrl.digital sys:is_a
set.add name="ontology.control_engineering" id="ctrl:z_transform"
