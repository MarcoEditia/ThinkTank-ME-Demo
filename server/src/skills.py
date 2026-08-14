import glob
from pathlib import Path
import asyncio
import os

from llama_index.core import (
    Settings, 
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    StorageContext,
    load_index_from_storage
)

import src.config

from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.node_parser import SimpleFileNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

SKILLS_DIR = Path(__file__).resolve().parents[1] / ".claude" / "skills"

async def _index_all_skills(vector_storage_directory: str | Path): 
    '''
        - Loads embedding model
        - Retrieve all the skill.md files from the .claude/skills/ directory
        - Turn all the documents(skill.md files) into nodes
        - Store the vectorized nodes

        returns index
    '''
    
    path = f"{SKILLS_DIR}/**/SKILL.md"
    skill_file_path = glob.glob(path, recursive=True)

    if(not skill_file_path):
       raise FileNotFoundError(f"No skills found in  {skill_file_path}, app cannot run without any claude skills")

    # load the skill.md files
    reader = SimpleDirectoryReader(input_files = skill_file_path)
    documents = reader.load_data()

    index = VectorStoreIndex(documents)
    index.storage_context.persist(persist_dir=vector_storage_directory)
    # turn documents into nodes
    # parser = SimpleFileNodeParser()
    # nodes = parser.get_nodes_from_documents(documents)

    # vectorize the nodes and store it
    # index = VectorStoreIndex(nodes)
    # index.storage_context.persist(persist_dir=vector_storage_directory)

    print(f"Index stored in {vector_storage_directory}")
       
async def retrieve_skill_index(vector_storage_directory: str | Path):
    '''
        - retrieves the claude skills index

        returns index
    '''

    storage_context = StorageContext.from_defaults(persist_dir=vector_storage_directory)

    # don't need to specify index_id if there's only one index in storage context else need to add the index_id = "<index_id>"
    index = load_index_from_storage(storage_context)

    return index

async def initialize_skill_index(
        vector_storage_directory: str | Path, 
        embedding_model: str, 
        embedding_model_path: str | None = None
):
    """
    Creates index if not exist yet
    """

    # Use the local path if provided, otherwise fall back to the HuggingFace hub string
    model_to_use = embedding_model_path if embedding_model_path else embedding_model
    Settings.embed_model = HuggingFaceEmbedding(model_name = model_to_use)

    # Check if files exist to load or create
    docstore_path = Path(vector_storage_directory) / "docstore.json"
    if Path(vector_storage_directory).exists() and docstore_path.exists():
        print(f"Loading existing index using model: {model_to_use}")
    else:
        print(f"Creating fresh index using model: {model_to_use}")
        await _index_all_skills(vector_storage_directory=vector_storage_directory)

async def retrieve_relevant_skill(prompt: str, index, k: int = 3):
    '''
        - retrieves the top k claude skills from the index based on the prompt 
        - extracts the folder_name from the metadata e.g /.claude/skills/{foldername} <-- extracts this

        returns the folder_name of the top k index type: list of Path
    '''

    # retrieve the similar index
    retriever = VectorIndexRetriever(
        index = index,
        similarity_top_k=k
    )
    response = retriever.retrieve(prompt)

    # extract the folder name (skill name)
    skill_names = []
    for r in response:
        folder_name = Path(r.metadata["file_path"]).parent.name
        skill_names.append(folder_name)

    return skill_names   

def load_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing skill: {path}")
    return path.read_text(encoding="utf-8")


# async def main():
#     await initialize_skill_index(
#         vector_storage_directory=config.settings.vector_index_storage, 
#         embedding_model=config.settings.embedding_model, 
#         embedding_model_path= config.settings.embedding_model_path
#     )

#     index = await retrieve_skill_index(vector_storage_directory=config.settings.vector_index_storage)
#     result = await retrieve_relevant_skill(prompt="US obtains Iranian enriched uranium by July 31?",index=index)

#     for i, n in enumerate(result):
#         print(f" skill no {i}: {n}")

# if __name__ == "__main__":
#     asyncio.run(main())


