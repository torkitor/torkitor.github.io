const form = document.querySelector('#publication-filters');
const papers = [...document.querySelectorAll('[data-publication]')];
const groups = [...document.querySelectorAll('.year-group')];
const normalise = text => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
const searchable = new Map(papers.map(paper => [paper, normalise(
  paper.textContent + ' ' + [...paper.querySelectorAll('a[href*="doi.org/"]')].map(link => link.href).join(' ')
)]));

function filterPublications() {
  const terms = normalise(form.elements.search.value.trim()).split(/\s+/).filter(Boolean);
  let count = 0;
  for (const paper of papers) {
    const matches = terms.every(term => searchable.get(paper).includes(term))
      && (!form.elements.year.value || paper.dataset.year === form.elements.year.value)
      && (!form.elements.topic.value || paper.dataset.topics.split('|').includes(form.elements.topic.value))
      && (!form.elements.first.checked || paper.dataset.first === 'true');
    paper.hidden = !matches;
    count += Number(matches);
  }
  for (const group of groups) {
    const visible = [...group.querySelectorAll('[data-publication]')].filter(paper => !paper.hidden).length;
    group.hidden = visible === 0;
    group.querySelector('h2 span').textContent = `${visible} ${visible === 1 ? 'publication' : 'publications'}`;
  }
  document.querySelector('#result-count').textContent = `${count} of ${papers.length} publications`;
  document.querySelector('#no-results').hidden = count !== 0;
}

const initialFilters = new URLSearchParams(window.location.search);
const initialTopic = initialFilters.get('topic');
if ([...form.elements.topic.options].some(option => option.value === initialTopic)) {
  form.elements.topic.value = initialTopic;
}
form.hidden = false;
form.addEventListener('input', filterPublications);
form.addEventListener('change', filterPublications);
form.addEventListener('submit', event => event.preventDefault());
document.querySelector('#reset-filters').addEventListener('click', () => {
  form.reset();
  filterPublications();
  form.elements.search.focus();
});
filterPublications();
