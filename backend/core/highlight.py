import os
from pathlib import Path
import fitz  # PyMuPDF
# import Document

from unstructured.partition.html import partition_html
def p_pdf(pdf_path: str):
    chunks = partition_html(
        # filename=pdf_path,
        url="https://docs.cohere.com/docs/advanced-prompt-engineering-techniques",
        strategy="fast",
        
        # Chunking settings for RAG
        chunking_strategy="by_title",                    # Options: "basic", "by_title", "by_page"
        max_characters=2048,                             # Maximum chunk size
        new_after_n_chars=1700,                          # Try to create new chunk after this many chars
        combine_text_under_n_chars=1000                  # Combine chunks smaller than this
    )
    docs = []
    print(chunks[0])
    print(f"Type: {type(chunks[0]).__name__}")
    
    # chunks = chunk_by_title(elements)
    for chunk in chunks:
        chunk = chunk.to_dict()
        # chunk["file_id"] = file_id
        # chunk["id"] = file_id
        # chunk['metadata']["title"] = raw_document["title"]
        docs.append(chunk)
    print(f"Keys: {docs[0].keys()} \nmetadata keys: {docs[0]['metadata'].keys()}")
    return docs

def highlight_pdf(file_path: str = "informer_arxiv.pdf", target_text: str = "", start:int=0, end:int=-1):
    # Load the PDF
    pdf_path = file_path
    doc = fitz.open(pdf_path)
    l = doc.get_page_images(9, full=True)
    print(l)

    # Loop through pages
    if end == -1:
        end = len(doc)
    for i in range(start, end, 1):
        page = doc[i]
        if i == start:
            print(f"Type page: {type(page).__name__} \tpage: {page}")
        text_instances = page.search_for(target_text)
        print(f"\nText instances: {text_instances}")

        # Highlight all instances found
        for inst in text_instances:
            print(f"Instance in Text Instances: {inst}")
            highlight = page.add_highlight_annot(inst)
            # bbox = fitz.Rect(inst)
            # highlight = page.add_highlight_annot(bbox)
            highlight.update()

    # Save the updated PDF
    path_pdf = Path(pdf_path)
    output_path = os.path.join(path_pdf.parent, f"{path_pdf.stem.split("/")[-1]}_highlighted.pdf")
    doc.save(output_path)
    extract_images(doc, idx=9, saved_path=f"{path_pdf.stem}")
    doc.close()
    
    print(f"Saved in: {output_path}")
    
    return doc
    
def extract_images(doc, idx, saved_path):
        im_list = doc.get_page_images(idx)
        print(f"Len images: {len(im_list)} \tType: {type(im_list[0]).__name__}")
        print(im_list[0])
        for img in im_list:
            pix = fitz.Pixmap(doc, img[0])
            if not pix.n - pix.alpha < 4:  # aka is cmyk
                pix = fitz.Pixmap(fitz.csRGB, pix)
            save_path = f"{saved_path}_{idx}.png"
            pix.save(save_path)
            
            pix = None
    
if __name__ == "__main__":
    target_text = "Univariate Time-series Forecasting Under this setting, "\
                "each method attains predictions as a single variable over "\
                "time series. From Table 1, we can observe that: (1) The proposed model Informer significantly"# significantly improves the inference"
                # "performance (wining-counts in the last column) across all "
                # "datasets, and their predict error rises smoothly and slowly "\
                # "within the growing prediction horizon, which demonstrates "\
                # "the success of Informer in enhancing the prediction capacity "\
                # "in the LSTF problem. (2) The Informer beats its canonical "\
                # "degradation Informer† mostly in wining-counts, i.e., 32>12,"
    docs = highlight_pdf(target_text=target_text, start=5, end=6)
    # extract_images(docs, idx=5, saved_path="informer_arxiv")
    
    # docs = p_pdf("informer_arxiv")
    