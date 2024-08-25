import time

def simple_training():
    print("Starting training...")
    for i in range(10):
        time.sleep(1)
        print(f"Training progress: {(i+1)*10}%")
    print("Training complete!")
    return 0.1  # Simulated final loss

if __name__ == "__main__":
    final_loss = simple_training()
    print(f"Final loss: {final_loss:.4f}")