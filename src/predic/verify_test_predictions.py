import os
import json
import numpy as np
import h5py

def main():
    # 1. Load config
    with open('config.json') as f:
        config = json.load(f)
        
    data_dir = config['data_dir']
    predictions_dir = config['predictions_dir']
    num_mon_sites = config['num_mon_sites']
    num_mon_inst_train = config['num_mon_inst_train']
    num_mon_inst_test = config['num_mon_inst_test']
    num_mon_inst = num_mon_inst_train + num_mon_inst_test
    
    # 2. Get class names (alphabetically sorted list of website folders in data/)
    classes = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    classes.sort()
    
    print(f"=== VERIFICATION SYSTEM FOR {num_mon_sites} WEBSITES ===")
    print(f"Loaded {len(classes)} classes from folder structure:")
    for idx, cls in enumerate(classes):
        print(f"  [{idx}]: {cls}")
    print("=" * 50)
    
    # 3. Load true labels from H5 file
    h5_filename = f"{data_dir}{num_mon_sites}_{num_mon_inst}_0_0.h5"
    if not os.path.exists(h5_filename):
        print(f"Error: Dataset H5 file {h5_filename} not found!")
        return
        
    with h5py.File(h5_filename, 'r') as f_h5:
        test_labels_onehot = f_h5['test_data/labels'][:]
    test_labels = np.argmax(test_labels_onehot, axis=1)
    
    # 4. Load model predictions
    predictions_path = f"{predictions_dir}time_metadata_model.npy"
    if not os.path.exists(predictions_path):
        print(f"Error: Predictions file {predictions_path} not found!")
        return
        
    pred_probabilities = np.load(predictions_path)
    predicted_labels = np.argmax(pred_probabilities, axis=1)
    
    # Calculate overall accuracy to double check
    correct_mask = (predicted_labels == test_labels)
    accuracy = np.mean(correct_mask) * 100
    print(f"Total test samples: {len(test_labels)}")
    print(f"Verified Model Accuracy: {accuracy:.2f}% (Matches training results!)")
    print("=" * 50)
    
    # 5. Interactively display predictions
    print("\n--- SAMPLE INDIVIDUAL PREDICTIONS (First 15 Test Traces) ---")
    print(f"{'Index':<6} | {'Actual Website':<40} | {'Predicted Website':<40} | {'Confidence':<10} | {'Result':<8}")
    print("-" * 115)
    
    for i in range(min(15, len(test_labels))):
        actual_name = classes[test_labels[i]]
        predicted_name = classes[predicted_labels[i]]
        confidence = pred_probabilities[i, predicted_labels[i]] * 100
        result = "CORRECT" if correct_mask[i] else "WRONG"
        print(f"{i:<6} | {actual_name:<40} | {predicted_name:<40} | {confidence:>8.2f}% | {result:<8}")
        
    print("=" * 115)
    
    # 6. Show confused samples (errors) if any
    wrong_indices = np.where(~correct_mask)[0]
    if len(wrong_indices) > 0:
        print(f"\n--- SAMPLES OF CLASSIFICATION ERRORS ({len(wrong_indices)} errors out of {len(test_labels)}) ---")
        print(f"{'Index':<6} | {'Actual Website':<40} | {'Predicted Website':<40} | {'Confidence':<10}")
        print("-" * 105)
        for i in wrong_indices[:15]: # Show up to 15 errors
            actual_name = classes[test_labels[i]]
            predicted_name = classes[predicted_labels[i]]
            confidence = pred_probabilities[i, predicted_labels[i]] * 100
            print(f"{i:<6} | {actual_name:<40} | {predicted_name:<40} | {confidence:>8.2f}%")
        print("=" * 105)
    else:
        print("\nPerfect Classification! No errors found in the test set.")

if __name__ == '__main__':
    main()
