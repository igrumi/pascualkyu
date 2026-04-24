const pokemonList = [];
document.querySelectorAll('.pokemon.thumbnail').forEach(el => {
    const imgElement = el.querySelector('img');
    const nameElement = el.querySelector('p');
    
    if (imgElement && nameElement) {
        pokemonList.push({
            name: nameElement.innerText.trim(),
            url: imgElement.src
        });
    }
});
console.log(JSON.stringify(pokemonList, null, 2));