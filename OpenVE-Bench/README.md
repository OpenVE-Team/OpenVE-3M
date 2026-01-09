## OpenVE-Bench

[OpenVE-Bench](https://huggingface.co/datasets/Lewandofski/OpenVE-Bench) is a new Instruction-Guided Video Editing benchmark contained 431 video-edit pairs that cover a diverse range of editing tasks with three key metrics highly aligned with human judgment. 

A folder containing original videos:

```folder
├── OpenVE-Bench                    
│   ├── videos     
|       |── 0000_global_style_Apply_the_Impression.mp4        
|       |── 0001_global_style_Apply_the_Ukiyoe_ani.mp4     
|       |── ...                 
│   ├── benchmark_videos.csv                             
```

`benchmark_videos.csv` contains following fields:

```
edited_type,prompt,original_video
```

## Generate and Organize Your Videos

Following the editing `prompt` in the `benchmark_videos.csv` file and the `original_video`, generate the video results for your model, and record the video paths in a new CSV `new_result.csv` file, adding a `edited_result_path` column at the end.

`new_result.csv` should contains following fields:

```
edited_type,prompt,original_video,edited_result_path
```

## Evaluate using Seed1.6VL/Gemini 2.5 Pro/InternVL3.5-38B/Qwen3VL-32B
For Seed1.6VL and Gemini 2.5 Pro, you should set your correct API key.

Seed 1.6 VL
```python
python seed_benchmark.py --input_csv new_result.csv --root_path yours_OpenVE-Bench_path --output_csv new_result_gemini_score.csv
```

Gemini 2.5 Pro
```python
python gemini_benchmark.py --input_csv new_result.csv --root_path yours_OpenVE-Bench_path --output_csv new_result_gemini_score.csv
```

[InternVL3.5-38B](https://huggingface.co/OpenGVLab/InternVL3_5-38B)
```python
python internvl_benchmark.py --input_csv new_result.csv --root_path yours_OpenVE-Bench_path --output_csv new_result_gemini_score.csv --model_path /yours_model_path/InternVL3.5-38B
```

[Qwen3VL-32B](https://huggingface.co/Qwen/Qwen3-VL-32B-Instruct)
```python
python qwen3vl_benchmark.py --input_csv new_result.csv --root_path yours_OpenVE-Bench_path --output_csv new_result_gemini_score.csv --model_path /yours_model_path/Qwen3VL-32B
```

*The final average metric results are in a JSON file.*