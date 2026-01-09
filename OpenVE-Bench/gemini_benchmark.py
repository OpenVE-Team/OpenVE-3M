 # Copyright (c) 2025 ByteDance Ltd. and/or its affiliates
 # SPDX-License-Identifier: Apache-2.0 
import argparse
import csv
import os
import torch
import torchvision.transforms as T
from PIL import Image
from tqdm import tqdm
import math
import numpy as np
import time
import argparse
import re
import json
import base64
import requests
import time

ak = ""
gemini_url = "" + ak
gemini_headers = {
    "Content-Type": "application/json",
    "X-TT-LOGID": ""
}

Global_Style = """\nYou are a data rater specializing in grading video style transfer edits. You will be given an input video, a reference style (image or video), and the styled result video. Your task is to evaluate the style transfer on a 5-point scale from three perspectives:\n\nStyle Fidelity\n1. Target style absent or clearly wrong.\n2. Style shows in a few areas/frames only, or mixed with unrelated styles.\n3. Key traits (palette, brushwork, texture) present but patchy or inconsistent across frames.\n4. Style reproduced well across almost the whole video; only small local or brief temporal mismatches.\n5. Full, faithful transfer: colour, texture, brushwork, and lighting all match the exemplar consistently over the entire duration and space of the video.\n\nContent Preservation\n1. Major objects, layout, or overall motion lost/distorted; original scene barely recognisable.\n2. Main subject recognisable, but its size, perspective, motion, or key parts are clearly wrong/missing.\n3. Overall structure and motion correct; some local warping, minor omissions, or slight motion jerkiness.\n4. Nearly all geometry and motion intact; only slight, non-distracting deformation.\n5. All objects, spatial relations, and motion are perfectly kept; only stylistic, harmless distortion.\n\nTemporal Stability\n1. Extreme flickering or "boiling" effects; the style is completely unstable frame-to-frame, making the video unwatchable.\n2. Significant and distracting flickering or temporal inconsistency in style application.\n3. Noticeable but tolerable flicker or texture "boiling", especially during motion.\n4. Largely stable with only minor, subtle flickering visible in areas of complex motion or fine texture.\n5. Perfectly stable and temporally coherent; the style appears "stuck" to the scene with no flickering.\n\nThe scores for Content Preservation and Temporal Stability should not be higher than the Style Fidelity score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the scores based on the criteria above, no more than 30 words.\nStyle Fidelity: A number from 1 to 5.\nContent Preservation: A number from 1 to 5.\nTemporal Stability: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:\n"""
Creative_Edit = """\nYou are a data rater specializing in grading instruction-following creative video edits. You will be given two videos (before and after editing) and the corresponding editing instructions. Your task is to evaluate the creative edit on a 5-point scale from three perspectives:\n\nPrompt Compliance\n1 The instruction is completely ignored or the edit is irrelevant to the prompt.\n2 The edit attempts the instruction but fundamentally fails; the core subject, style, or action is wrong or only applied for a brief moment.\n3 The edit generally follows the instruction, but with major deviations in style, motion, or concept; the effect is highly inconsistent over time.\n4 The edit successfully executes the instruction with only minor inaccuracies in style, motion, or detail; the result is temporally consistent.\n5 The edit perfectly and creatively interprets and executes the instruction throughout the video's duration, fully achieving the intended creative goal.\n\nTemporal & Visual Coherence\n1 Massive flickering, strobing, or artifacts that make the video unwatchable; edited elements are completely disjointed from the scene.\n2 Obvious temporal inconsistency (e.g., style flickers on/off), clear visual boundaries or seams; mismatched color/lighting between frames.\n3 The edit is mostly stable, but with noticeable "boiling" or "shimmering" in textures/styles; minor jitter or softness on edges.\n4 The edit is very stable and well-integrated; only slight, hard-to-spot artifacts or flickering are present, motion is smooth.\n5 Perfectly stable and seamless integration; the edit feels like part of the original footage with no detectable flickering, jitter, or discontinuities.\n\nPhysical Plausibility & Detail Preservation\n1 Complete break from physical laws; added objects have no correct lighting/shadows, move unnaturally; original video details are heavily degraded.\n2 Major physical inconsistencies; shadows/reflections are static or move incorrectly; motion of edits doesn't match camera movement; original background is warped.\n3 Physics and lighting are generally believable but with minor flaws (e.g., a shadow is slightly off); unedited parts of the video are mostly preserved.\n4 Edited elements interact realistically with the scene's lighting, motion, and perspective; original video details are well-preserved.\n5 High degree of physical realism and integration; motion, lighting, and physics of the edits are indistinguishable from a real recording; original details are perfectly maintained.\nThe second and third score should no higher than first score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the score based on the criteria above, no more than 20 words.\nPrompt Compliance: A number from 1 to 5.\nTemporal & Visual Coherence: A number from 1 to 5.\nPhysical Plausibility & Detail Preservation: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:\n"""
Camera_Edit = """\nYou are a data rater specializing in grading camera shot type alteration edits. You will be given two videos (before and after editing) and the corresponding editing instructions. Your task is to evaluate the camera shot change on a 5-point scale from three perspectives:\n\nPrompt Compliance\n1 The shot type is not changed, or changed to a completely wrong type (e.g., requested close-up, but got a long shot).\n2 The direction of the shot change is correct (e.g., zoomed in for a close-up), but the degree is wrong (e.g., a medium shot instead of a close-up).\n3 The shot type is generally correct, but the framing is poor, cutting off important parts of the subject or being poorly centered.\n4 The shot type and framing are correct, with only minor inaccuracies in composition.\n5 The video is perfectly transformed into the requested shot type (long, medium, or close-up) with ideal framing of the subject.\n\nVisual Quality & Stability\n1 Massive distortion, glitches, warping, or heavy noise; the edited video is unusable.\n2 Significant and distracting jitter, shimmering, or warping is visible throughout the video, making the shot feel unstable.\n3 Minor but noticeable visual flaws, such as slight edge distortion or a subtle "breathing" effect in the frame.\n4 The video is stable and clear, with only very slight, almost unnoticeable artifacts upon close inspection.\n5 The resulting shot is perfectly stable and clear, with no digital artifacts, distortion, or jitter. It looks as if it were originally filmed with that shot type.\n\nConsistency & Detail Fidelity\n1 The subject, background, or action in the edited video is completely different from the original video; a total failure of consistency.\n2 The main subject is the same, but their action, the background, or the lighting is drastically and illogically changed compared to the original video.\n3 The scene is generally consistent, but there are noticeable continuity errors (e.g., an object disappears, the subject's pose changes unnaturally).\n4 The subject, action, and environment are highly consistent with the original video. Original details are well-preserved with only minor, hard-to-spot discrepancies.\n5 Perfect consistency; the edited video perfectly preserves the subject, lighting, background, and continuity of action from the original video, creating the illusion of the same scene captured from a different camera position.\nThe second and third score should no higher than first score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the score based on the criteria above, no more than 20 words.\nPrompt Compliance: A number from 1 to 5.\nVisual Quality & Stability: A number from 1 to 5.\nConsistency & Detail Fidelity: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:\n"""
Local_Change = """\nYou are a data rater specializing in grading video replacement edits. You will be given two videos (before and after editing) and the corresponding editing instructions. Your task is to evaluate the replacement editing effect on a 5-point scale from three perspectives, paying close attention to temporal consistency (how the edit holds up over time and with motion).\n\nPrompt Compliance\n1 Target not replaced, or an unrelated object/part of the video edited.\n2 Only part of the target replaced (e.g., in only a few frames), or wrong class/description used.\n3 Target largely replaced but other objects altered, remnants visible across frames, or count/position clearly wrong.\n4 Correct object fully replaced for the entire duration; only minor attribute errors (colour, size, etc.).\n5 Perfect replacement: all and only the specified objects replaced for the entire duration; new objects’ class, number, position, scale, pose, motion and detail exactly match the prompt.\n\nVisual Naturalness & Temporal Stability\n1 Video heavily broken or new object deformed / flickers uncontrollably / jitters erratically.\n2 Obvious seams/edges that flicker or move unnaturally; strong mismatch in resolution or colour that is inconsistent across frames; background not restored or is unstable.\n3 Basic style similar, but lighting or palette clashes are inconsistent as the video plays; fuzzy edges, noise or minor flickering/jittering are noticeable.\n4 Style almost uniform and stable; tiny temporal artefacts (e.g., edge shimmer) visible only on close, frame-by-frame inspection; casual viewers see no edit.\n5 Completely seamless and temporally stable; new objects blend fully with the scene in every frame, edit area undetectable.\n\nPhysical & Motion Integrity\n1 Floating or sliding unnaturally (poor motion tracking), severe perspective/light errors inconsistent with camera/object movement; background heavily warped or unstable.\n2 Missing or static shadows/reflections that do not move with the object/light; poor occlusion; new object’s motion clearly mismatches scene motion.\n3 Lighting, perspective and interactions mostly correct but with minor inconsistencies over time; motion tracking has small, tolerable drifts.\n4 New object's motion is well-tracked and it interacts realistically with the scene (shadows, reflections) and preserves existing details throughout the video.\n5 Physically and dynamically flawless: motion, perspective, shadows, and reflections are perfectly integrated and move correctly with the scene and camera in every frame; background untouched and stable.\nThe second and third score should no higher than first score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the score based on the criteria above, no more than 20 words.\nPrompt Compliance: A number from 1 to 5.\nVisual Naturalness & Temporal Stability: A number from 1 to 5.\nPhysical & Motion Integrity: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:\n"""
Background_Change = """\nYou are a data rater specializing in grading video background editing. You will be given two videos (before and after editing) and the editing instruction. Your task is to evaluate the background change on a 5-point scale from three perspectives:\n\nInstruction Compliance\n1 No change, or background unrelated to prompt, or foreground also replaced/distorted.\n2 Background partly replaced or wrong style/content; foreground noticeably altered.\n3 Main background replaced but elements missing/extra, or faint spill onto subject edges.\n4 Requested background fully present; foreground intact except minute artefacts or small prompt mismatch (e.g. colour tone).\n5 Background exactly matches prompt (content, style, placement); all foreground pixels untouched.\n\nVisual & Temporal Seamlessness (Edge, Blend & Stability)\n1 Large tearing, posterisation, or significant temporal artifacts like flickering, jittering edges; edit area obvious at a glance.\n2 Clear cut-out halos, colour-resolution gap, or obvious edge 'boiling' (instability) over time.\n3 Blend acceptable but visible on closer look: slight edge blur, or minor temporal instability (e.g., shimmer).\n4 Nearly invisible seams; edges are stable across motion, textures aligned, only minor issues when zoomed in.\n5 Indistinguishable composite: edges, textures, resolution and colour grading are perfectly continuous and stable throughout the video's duration.\n\nPhysical Consistency (Lighting, Perspective, Motion & Depth)\n1 Severe mismatch: wrong horizon, conflicting light, floating subject, or background remains static during camera movement (no parallax).\n2 Noticeable inconsistencies in light or scale; incorrect perspective shifts during motion.\n3 Overall believable; small errors in shadow, perspective, or minor motion tracking flaws.\n4 Lighting, scale, and depth well matched; background perspective and scale track convincingly with camera motion.\n5 Physically flawless: foreground and new background share coherent light, shadows, perspective, and atmospheric depth throughout all subject and camera motion, enhancing overall realism.\nThe second and third score should no higher than first score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the score based on the criteria above, no more than 20 words.\nInstruction Compliance: A number from 1 to 5.\nVisual & Temporal Seamlessness: A number from 1 to 5.\nPhysical Consistency: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:\n"""
Local_Remove = """\nYou are a data rater specializing in grading video object removal editing. You will be given two videos (before and after editing) and the corresponding editing instructions. Your task is to evaluate the edit quality on a 5-point scale from three perspectives:\n\nPrompt Compliance\n1 No edit performed, the video is corrupted, or the edit is completely wrong.\n2 Wrong object/class removed, or target only partially removed, or an unrelated object is also removed.\n3 Correct object removed, but with significant errors: unintended objects are also removed, OR significant fragments/ghosting of the target remain.\n4 The correct object is removed; only minor issues like a few tiny fragments remaining or tiny, unintended background items being affected.\n5 Perfect: All and only the requested objects are removed as instructed; every other element is untouched.\n\nVisual & Temporal Naturalness\n1 Video is badly broken, full of artefacts, or shows severe flickering/jittering throughout.\n2 Obvious erase marks or "smudges"; the inpainted background's style, resolution, or palette strongly mismatches; the edited region jitters or appears static against a moving background.\n3 General style is similar, but the inpainted background's lighting/colours clearly clash or are inconsistent across frames; noticeable temporal disharmony.\n4 Style is almost uniform; minor edge issues around the removed area or slight temporal instability (e.g., minor flicker) visible only on close inspection.\n5 Perfectly seamless; the removal is temporally stable and visually indistinguishable from a clean background.\n\nPhysical & Detail Coherence\n1 Key original elements are blocked by poor inpainting; the background is heavily distorted or hallucinates incorrect structures; motion is completely wrong (e.g., a static patch in a moving scene).\n2 The inpainted background visibly shifts, jitters, or is poorly reconstructed over time, failing to match the original scene's motion.\n3 Background reconstruction is mostly correct and consistent; remaining flaws are small and acceptable; background changes are localized and stable.\n4 No loss of original detail around the removed area; background reconstruction is clean, stable, and respects the scene's geometry and motion.\n5 The background is essentially untouched and stable; the inpainted area perfectly matches the surrounding content's motion, texture, and detail over time.\n\nThe second and third score should no higher than first score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the score based on the criteria above, no more than 20 words.\nPrompt Compliance: A number from 1 to 5.\nVisual & Temporal Naturalness: A number from 1 to 5.\nPhysical & Detail Coherence: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:"""
Local_Add = """\nYou are a data rater specializing in grading video object addition editing. You will be given two videos (before and after editing) and the corresponding editing instructions. Your task is to evaluate the edit quality on a 5-point scale from three perspectives:\n\nPrompt Compliance\n1 No edit performed, the video is corrupted, or the edit is completely wrong.\n2 Wrong object/class added, or target only partially added, or an unrelated object is also added.\n3 Correct object added, but with significant errors: key attributes (e.g., position, colour, count, size) are wrong.\n4 The correct object is added with main attributes correct; only minor details are off (e.g., slight colour mismatch, minor position error).\n5 Perfect: All and only the requested objects are added as instructed; every other element is untouched.\n\nVisual & Temporal Naturalness\n1 Video is badly broken, full of artefacts, or shows severe flickering/jittering throughout.\n2 Obvious paste marks; style, resolution, or palette of the added object strongly mismatches; the added region jitters or appears static against a moving background.\n3 General style is similar, but lighting/colours on the added object clearly clash or are inconsistent across frames; noticeable temporal disharmony.\n4 Style is almost uniform; minor edge issues around the added object or slight temporal instability (e.g., minor flicker) visible only on close inspection.\n5 Perfectly seamless; the edit is temporally stable and visually indistinguishable from the original video's content and motion.\n\nPhysical & Detail Coherence\n1 Severe physical errors (e.g., the added object floats, has wrong perspective/lighting); key original elements are blocked; motion of the added object is completely wrong.\n2 Contact with surfaces, occlusion by other objects, or motion of the added object is handled poorly.\n3 Lighting, perspective, and motion of the added object are mostly correct and consistent with the scene; remaining flaws are small and acceptable.\n4 Shadows, reflections, and material response from the added object are believable and move correctly with the scene; no loss of original detail.\n5 Edit enhances overall realism: the added object has precise highlights, shadows, and motion effects that are temporally coherent and perfectly integrated.\n\nThe second and third score should no higher than first score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the score based on the criteria above, no more than 20 words.\nPrompt Compliance: A number from 1 to 5.\nVisual & Temporal Naturalness: A number from 1 to 5.\nPhysical & Detail Coherence: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:"""
Subtitle_Edit = """"\nYou are a data rater specializing in grading instruction-following subtitle edits. You will be given two videos (before and after editing) and the corresponding editing instructions. Your task is to evaluate the subtitle edit on a 5-point scale from three perspectives:\n\nPrompt Compliance\n1 Target subtitle not added/removed/replaced, or wrong subtitle affected.\n2 Right action (add/remove/replace) but with incorrect content; only part of the edit is done; other subtitles are also altered.\n3 Mainly correct action and content, yet with significant spelling/grammar errors, or minor unintended edits to other subtitles.\n4 Correct action performed on the right subtitle; content is correct with only minor inaccuracies (e.g., small typos, punctuation errors).\n5 Exactly and only the requested subtitle(s) are added/removed/replaced; content matches the prompt perfectly; zero unintended edits.\n\nSubtitle Attribute Fidelity\n1 Completely fails to follow specified attributes (e.g., wrong position, wrong color). If attributes are not specified, the chosen ones make the subtitle unreadable or are extremely disruptive.\n2 Major deviation from specified attributes (e.g., requested bottom, placed on top). If not specified, chosen attributes are clearly wrong and distracting (e.g., obscures key visuals).\n3 Follows the general direction of specified attributes but with significant errors (e.g., correct side but wrong exact position). If not specified, chosen attributes are acceptable but noticeably inconsistent.\n4 Follows specified attributes with only minor inaccuracies (e.g., slightly off-center, minor deviation in font/color). If not specified, chosen attributes are highly appropriate with only minor flaws.\n5 All specified attributes (position, font, color, etc.) are matched perfectly. If attributes are not specified, the chosen ones are perfectly consistent with existing subtitles or professional standards.\n\nIntegrity of Unedited Content\n1 Massive collateral damage: background video is heavily corrupted/glitched, or other non-target subtitles are wrongly deleted/altered.\n2 Noticeable collateral damage: visible artifacts, distortion, or color shifts in the background video; other subtitles are visibly affected.\n3 Minor unintended effects: slight and localized visual artifacts in the background, or minor, non-critical changes to adjacent subtitles' appearance/timing.\n4 Almost perfect preservation: only extremely subtle artifacts in the video frame, visible only upon close inspection; all other subtitles are untouched.\n5 Perfect preservation: the edit is perfectly isolated; the background video and all other subtitles remain 100% identical to the original, with zero unintended changes.\nThe second and third score should no higher than first score!!!\n\nExample Response Format:\nBrief reasoning: A short explanation of the score based on the criteria above, no more than 20 words.\nPrompt Compliance: A number from 1 to 5.\nSubtitle Attribute Fidelity: A number from 1 to 5.\nIntegrity of Unedited Content: A number from 1 to 5.\nediting instruction is : <edit_prompt>.\n\nBelow are the videos before and after editing:\n"""


def extract_scores_and_average(entry: str) -> float:
    import re
    
    pattern = r':\s*(\d+\.?\d*)'
    matches = re.findall(pattern, entry)
    
    scores = []
    for match in matches:
        try:
            scores.append(float(match))
        except ValueError:
            continue
    
    if scores:
        return round(sum(scores) / len(scores), 2)
    return None


def call_gemini_model(original_video_path, edited_video_path, prompt):
    global gemini_headers, gemini_url
    
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            user_content = [{"type": "text", "text": prompt.strip()}]
            
            # Process Original Video
            if os.path.exists(original_video_path):
                with open(original_video_path, "rb") as video_file:
                    base64_video = base64.b64encode(video_file.read()).decode('utf-8')
                user_content.append(
                    {"type": "image_url", "image_url": {"url": f"data:video/mp4;base64,{base64_video}"}}
                )
            else:
                user_content.append(
                    {"type": "image_url", "image_url": {"url": original_video_path}}
                )
            
            # Process Edited Video
            if os.path.exists(edited_video_path):
                with open(edited_video_path, "rb") as video_file:
                    base64_video = base64.b64encode(video_file.read()).decode('utf-8')
                user_content.append(
                    {"type": "image_url", "image_url": {"url": f"data:video/mp4;base64,{base64_video}"}}
                )
            else:
                user_content.append(
                    {"type": "image_url", "image_url": {"url": edited_video_path}}
                )

            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_content},
            ]

            payload = {
                "max_tokens": 8192,
                "messages": messages,
                "model": "gemini-2.5-pro-preview-05-06",
                "temperature": 0.7,
                "stream": False
            }

            response = requests.post(gemini_url, headers=gemini_headers, data=json.dumps(payload), timeout=120)
            result = json.loads(response.text)

            if response.status_code == 200:
                if "choices" in result and result["choices"]:
                    for message in result["choices"]:
                        try:
                            message = message.get("message", {})
                            content = message.get("content", "")
                            if retry_count > 0:
                                logging.info(f"The Gemini call succeeded, and it was retried {retry_count} times.")
                            return content
                        except Exception as e:
                            logging.error(f"Error extracting content: {e}")
                            continue
                    return f"ERROR: No valid content found in choices - {result}"
                else:
                    error_msg = f"ERROR: No choices in response - {result}"
                    logging.warning(f"Retry for {retry_count + 1}th time: {error_msg}")
                    retry_count += 1
                    time.sleep(60)
                    continue
            else:
                error_msg = f"ERROR: call Gemini failed, status code: {response.status_code}, response: {result}"
                logging.warning(f"Retry for {retry_count + 1}th time: {error_msg}")
                retry_count += 1
                time.sleep(60)
                continue
                
        except Exception as e:
            error_msg = f"An error occurred while calling the Gemini model.: {e}"
            logging.warning(f"Retry for {retry_count + 1}th time: {error_msg}")
            retry_count += 1
            time.sleep(60)
            continue


def process_csv(input_csv_path, output_csv_path, root_path, edited_video_path="edited_result_path"):
    start = time.time()
    all_scores_by_type = {}
    all_scores = []
    
    with open(input_csv_path, 'r', encoding='utf-8-sig') as infile, \
        open(output_csv_path, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile, delimiter=',')
        
        header = reader.fieldnames
        writer.writerow(header + ['results', 'average'])
        
        for row_idx, row in enumerate(tqdm(reader, desc=f"Processing {os.path.basename(input_csv_path)}")):
            try:
                edited_type = row.get('edited_type', '')
                prompt = row.get('prompt', '')
                original_video = row.get('original_video', '')
                edited_result_path = row.get(edited_video_path, '')

                original_video = os.path.join(root_path, original_video)
                
                if not os.path.exists(edited_result_path):
                    print(f"Warning: The edited video file does not exist.: {edited_result_path}")
                    original_row = [row.get(col, '') for col in header]
                    writer.writerow(original_row + [f"ERROR: Video file not found: {edited_result_path}", "ERROR"])
                    continue

                if not os.path.exists(original_video):
                    print(f"Warning: The original video file does not exist.: {original_video}")
                    original_row = [row.get(col, '') for col in header]
                    writer.writerow(original_row + [f"ERROR: Video file not found: {original_video}", "ERROR"])
                    continue
                
                if edited_type == "global_style":
                    system_prompt = Global_Style
                elif edited_type == "local_change":
                    system_prompt = Local_Change
                elif edited_type == "background_change":
                    system_prompt = Background_Change
                elif edited_type == "subtitle_edit":
                    system_prompt = Subtitle_Edit
                elif edited_type == "local_remove":
                    system_prompt = Local_Remove
                elif edited_type == "local_add":
                    system_prompt = Local_Add
                elif edited_type == "creative_edit":
                    system_prompt = Creative_Edit
                elif edited_type == "camera_edit":
                    system_prompt = Camera_Edit
                else:
                    raise ValueError("Invalid edit type")

                full_system_prompt = system_prompt.replace('<edit_prompt>', prompt)
                
                print(f"The Gemini model is being used for evaluation.... (行 {row_idx + 1})")
                response = call_gemini_model(original_video, edited_result_path, full_system_prompt)
                
                formatted_response = response.replace('\n', '\\n')
                
                # Calculate the average value
                average_score = extract_scores_and_average(response)
                
                # Write the original data, results, and average value onto a new line
                original_row = [row.get(col, '') for col in header]
                writer.writerow(original_row + [formatted_response, average_score])
                
                # Record the scores for subsequent statistics
                if average_score is not None:
                    all_scores.append(average_score)
                    
                    # Grouped by editing type
                    if edited_type not in all_scores_by_type:
                        all_scores_by_type[edited_type] = []
                    all_scores_by_type[edited_type].append(average_score)
                
            except Exception as e:
                print(f"\nError: An error occurred while processing row {row}: {e}")
                original_row = [row.get(col, '') for col in header]
                writer.writerow(original_row + [f"ERROR: {e}", "ERROR"])

    
    # Calculate the average score for different editing types (only scores in the range of 1-5 are counted).
    type_averages = {}
    for edited_type, scores in all_scores_by_type.items():
        valid_scores = [score for score in scores if 1 <= score <= 5]
        if valid_scores:
            type_averages[edited_type] = round(sum(valid_scores) / len(valid_scores), 2)
        else:
            type_averages[edited_type] = None

    # Calculate the overall average score (only scores in the range of 1-5 are counted).
    overall_average = None
    valid_all_scores = [score for score in all_scores if 1 <= score <= 5]
    if valid_all_scores:
        overall_average = round(sum(valid_all_scores) / len(valid_all_scores), 2)

    # Save the statistical results to a JSON file
    stats_output_path = output_csv_path.replace('.csv', '_stats.json')
    stats_data = {
        "overall_average": overall_average,
        "type_averages": type_averages,
        "total_processed": len(all_scores),
        "total_valid_scores": len(valid_all_scores),
        "breakdown_by_type": {}
    }

    # Calculate detailed statistics for each type
    for k, v in all_scores_by_type.items():
        valid_scores_for_type = [score for score in v if 1 <= score <= 5]
        stats_data["breakdown_by_type"][k] = {
            "count": len(valid_scores_for_type),
            "average": round(sum(valid_scores_for_type) / len(valid_scores_for_type), 2) if valid_scores_for_type else None,
            "original_count": len(v),  
            "invalid_count": len(v) - len(valid_scores_for_type)  # Number of invalid data
        }
    
    with open(stats_output_path, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nProcessing complete! Results saved to: {output_csv_path}")
    print(f"Statistical results saved to: {stats_output_path}")
    print(f"Average score for each editing type: {type_averages}")
    print(f"Overall average score: {overall_average}")
    print(f'Time for total: {time.time()-start} seconds')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use the Gemini 2.5 Pro model to process video and prompt CSV files.")
    parser.add_argument("--input_csv", type=str, default="benchmark/your_model_out.csv", help="The path to the input CSV file.")
    parser.add_argument("--root_path", type=str, default="yours_OpenVE-Bench_path", help="The path to the OpenVE-Bench videos.")
    parser.add_argument("--output_csv", type=str, default="benchmark/your_model_out_gemini.csv", help="The path to the output CSV file.")
    args = parser.parse_args()
    
    output_dir = os.path.dirname(args.output_csv)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    process_csv(args.input_csv, args.output_csv, args.root_path, edited_video_path="edited_result_path")
