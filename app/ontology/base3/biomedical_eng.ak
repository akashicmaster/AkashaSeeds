# Akasha ontology — biomedical / medical engineering.
# Where engineering meets medicine — devices, imaging, prosthetics, biosignals,
# and brain-computer interfaces. Bridged to med:/rehab:/neuro:/electron:. Base pack.

def "bme" "Biomedical engineering — engineering applied to medicine and biology (生体医工学)."
ln bme med:medicine thesaurus:related
ln bme electron thesaurus:related

def "bme:medical_device" "An instrument or apparatus used to diagnose or treat (医療機器)."
ln bme:medical_device bme thesaurus:related
def "bme:medical_imaging" "Technologies that image the body — the domain of radiology."
ln bme:medical_imaging bme thesaurus:related
ln bme:medical_imaging med:specialty:radiology thesaurus:related
ln bme:medical_imaging dh:3d_modeling thesaurus:related
def "bme:mri" "Magnetic resonance imaging — soft-tissue imaging by magnetic fields (MRI)."
ln bme:mri bme thesaurus:related
ln bme:mri med:specialty:radiology thesaurus:related
ln bme:mri neuro:cerebral_cortex thesaurus:related
def "bme:ct_scan" "Computed tomography — cross-sectional X-ray imaging (CT)."
ln bme:ct_scan bme thesaurus:related
ln bme:ct_scan med:specialty:radiology thesaurus:related
def "bme:ultrasound" "Imaging by high-frequency sound (超音波)."
ln bme:ultrasound bme thesaurus:related
def "bme:biosensor" "A sensor detecting a biological signal or analyte (バイオセンサ)."
ln bme:biosensor bme thesaurus:related
ln bme:biosensor electron:sensor thesaurus:related
ln bme:biosensor nutrisci:biomarker thesaurus:related
def "bme:bioinstrumentation" "Instruments measuring physiological signals."
ln bme:bioinstrumentation bme thesaurus:related
ln bme:bioinstrumentation electron:signal_processing thesaurus:related
def "bme:biosignal" "A signal from the body — ECG, EEG, EMG."
ln bme:biosignal bme thesaurus:related
def "bme:ecg" "Electrocardiogram — the heart's electrical activity."
ln bme:ecg bme thesaurus:related
ln bme:ecg med:specialty:cardiology thesaurus:related
def "bme:eeg" "Electroencephalogram — the brain's electrical activity."
ln bme:eeg bme thesaurus:related
ln bme:eeg neuro:neuron thesaurus:related
ln bme:eeg electron:signal_processing thesaurus:related
def "bme:biomechanics" "Mechanics applied to living bodies — gait, joints, load (生体力学)."
ln bme:biomechanics bme thesaurus:related
ln bme:biomechanics mecheng:mechanics_of_materials thesaurus:related
ln bme:biomechanics rehab:mobility_training thesaurus:related
def "bme:biomaterial" "A material designed to interface with living tissue (生体材料)."
ln bme:biomaterial bme thesaurus:related
def "bme:tissue_engineering" "Growing functional tissue to repair the body (組織工学)."
ln bme:tissue_engineering bme thesaurus:related
def "bme:implant" "A device placed in the body (インプラント)."
ln bme:implant bme thesaurus:related
ln bme:implant bme:biomaterial thesaurus:related
def "bme:pacemaker" "An implant regulating the heartbeat."
ln bme:pacemaker bme thesaurus:related
ln bme:pacemaker med:specialty:cardiology thesaurus:related
ln bme:pacemaker electron:microcontroller thesaurus:related
def "bme:artificial_organ" "An engineered device replacing an organ's function (人工臓器)."
ln bme:artificial_organ bme thesaurus:related
ln bme:artificial_organ med:medicine thesaurus:related
def "bme:prosthetics_eng" "Engineering of artificial limbs and their control."
ln bme:prosthetics_eng bme thesaurus:related
ln bme:prosthetics_eng rehab:prosthetics thesaurus:related
ln bme:prosthetics_eng mecheng:actuator thesaurus:related
def "bme:rehabilitation_engineering" "Engineering assistive and rehab technology (リハビリ工学)."
ln bme:rehabilitation_engineering bme thesaurus:related
ln bme:rehabilitation_engineering rehab:assistive_technology thesaurus:related
ln bme:rehabilitation_engineering special:accessibility thesaurus:related
def "bme:brain_computer_interface" "A direct link between brain signals and machines (BCI/ブレイン・マシン・インターフェース)."
ln bme:brain_computer_interface bme thesaurus:related
ln bme:brain_computer_interface neuro:neuron thesaurus:related
ln bme:brain_computer_interface neuro:hippocampus thesaurus:related
ln bme:brain_computer_interface ai:embedding thesaurus:related
ln bme:brain_computer_interface electron:signal_processing thesaurus:related
def "bme:medical_robotics" "Robots for surgery, rehab and care."
ln bme:medical_robotics bme thesaurus:related
ln bme:medical_robotics electron:actuator thesaurus:related
ln bme:medical_robotics med:specialty:surgery thesaurus:related
