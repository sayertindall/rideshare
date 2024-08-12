import uuid
import csv
import random
import hashlib
import faker
import nltk
import time
import mesa
from nltk.corpus import wordnet
from collections import defaultdict
from typing import List, Dict, Any, Tuple

# Download necessary NLTK data
nltk.download('wordnet', quiet=True)
fake = faker.Faker()

VERBOSE = True  # Set this to False to turn off print statements

def vprint(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)

# Configuration and initialization
class Config:
    def __init__(self):
        self.simulation_duration = 30  # in simulated days
        self.knowledge_decay_threshold = 30  # days before decay starts
        self.knowledge_decay_rate = 0.01  # per day after threshold
        self.knowledge_value_multiplier = 10
        self.query_fee = 0.1
        self.validator_reward_percentage = 0.2
        self.provider_reward_percentage = 0.6
        self.supporter_reward_percentage = 0.2
        self.time_scale = 10000  # 1 simulated day = 1 real second
        self.record_data = True

config = Config()

class DriaL2:
    def __init__(self, batch_token):
        self.batch_token = batch_token
        self.base_fee = 1
        self.priority_fee = 0.5

    def process_transaction(self, transaction):
        gas_fee = self.calculate_gas_fee(transaction)
        if self.batch_token.transfer(transaction['sender'], 'fee_pool', gas_fee):
            if transaction['type'] == 'knowledge_upload':
                vprint(f"DriaL2: Processed knowledge upload for {transaction['knowledge_id']}")
            elif transaction['type'] == 'query':
                vprint(f"DriaL2: Processed query for {transaction['seeker_id']}")
            return True
        else:
            return False

    def calculate_gas_fee(self, transaction):
        return self.base_fee + self.priority_fee + (0.01 * len(str(transaction)))  # Added data fee

class Librarian:
    def __init__(self):
        self.indices = {}
        self.context_tree = {}

    def add_index(self, index_id, knowledge):
        self.indices[index_id] = knowledge
        self.update_context_tree(index_id, knowledge)

    def update_context_tree(self, index_id, knowledge):
        topic = knowledge['topic']
        words = topic.lower().split()
        for word in words:
            if word not in self.context_tree:
                self.context_tree[word] = set()
            self.context_tree[word].add(index_id)

    def search(self, query):
        query_words = query.lower().split()
        relevant_indices = set()
        for word in query_words:
            if word in self.context_tree:
                relevant_indices.update(self.context_tree[word])
        results = [(index_id, self.indices[index_id]) for index_id in relevant_indices]
        return sorted(results, key=lambda x: x[1]['value'], reverse=True)

class DKN:
    def __init__(self, knowledge_registry):
        self.knowledge_registry = knowledge_registry
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def aggregate_results(self, results):
        return sum(results) / len(results) if results else 0

    def process_task(self, task):
        results = [node.compute(task) for node in self.nodes]
        aggregated_result = self.aggregate_results(results)
        return aggregated_result  # Remove the verify_result call here

    def verify_result(self, result):
        if isinstance(result, dict):
            return result.get('score', 0) > 0.5
        elif isinstance(result, (int, float)):
            return result > 0.5
        else:
            return False  # or handle other types as needed

class SyntheticDataGenerator:
    def __init__(self, librarian):
        self.librarian = librarian

    def generate_data(self, topic, bias_config):
        rationale = self.generate_rationale(topic)
        grounding_examples = self.librarian.search(topic)
        content = self.generate_content(rationale, grounding_examples)
        biased_content = self.apply_bias(content, bias_config)
        return {
            "topic": topic,
            "content": biased_content,
            "creation_time": time.time(),
            "value": random.randint(10, 100) * config.knowledge_value_multiplier,
            "usage_count": 0,
            "rating": 0
        }

    def generate_rationale(self, topic):
        return f"Generate comprehensive and factual content about {topic}"

    def generate_content(self, rationale, grounding_examples):
        content = f"{rationale}. "
        for _, example in grounding_examples[:3]:
            content += f"{example['content'][:100]}... "
        return content

    def apply_bias(self, content, bias_config):
        bias_type = bias_config['bias_type']
        if bias_type == 'positive':
            return f"{content} This topic has many beneficial aspects and positive implications."
        elif bias_type == 'negative':
            return f"{content} However, this topic also presents several challenges and potential drawbacks."
        else:
            return content

class EconomicModel:
    def __init__(self, initial_supply, initial_price):
        self.token_supply = initial_supply
        self.token_price = initial_price
        self.demand = initial_supply
        self.liquidity = initial_supply * initial_price

    def update(self, new_demand):
        self.demand = new_demand
        self.token_price = self.liquidity / self.token_supply
        if self.demand > self.token_supply:
            self.mint_tokens(self.demand - self.token_supply)
        elif self.demand < self.token_supply:
            self.burn_tokens(self.token_supply - self.demand)

    def mint_tokens(self, amount):
        self.token_supply += amount
        self.liquidity += amount * self.token_price

    def burn_tokens(self, amount):
        self.token_supply -= amount
        self.liquidity -= amount * self.token_price

class BatchToken:
    def __init__(self, initial_supply, economic_model):
        self.total_supply = initial_supply
        self.balances = defaultdict(float)
        self.economic_model = economic_model
        self.balances['fee_pool'] = initial_supply  # Initialize fee_pool with all tokens

    def allocate_initial_balance(self, address, amount):
        if self.total_supply >= amount:
            self.balances[address] = amount
            self.total_supply -= amount
            return True
        return False

    def transfer(self, sender, recipient, amount):
        if self.balances[sender] >= amount:
            self.balances[sender] -= amount
            self.balances[recipient] += amount
            return True
        return False

    def burn(self, account, amount):
        if self.balances[account] >= amount:
            self.balances[account] -= amount
            self.total_supply -= amount
            self.economic_model.burn_tokens(amount)
            return True
        return False

    def mint(self, recipient, amount):
        self.total_supply += amount
        self.balances[recipient] += amount
        self.economic_model.mint_tokens(amount)
        return True

class KnowledgeSupportToken:
    def __init__(self, knowledge_id, provider_id):
        self.knowledge_id = knowledge_id
        self.provider_id = provider_id
        self.total_supply = 0
        self.balances = defaultdict(float)

    def mint(self, supporter, amount):
        self.total_supply += amount
        self.balances[supporter] += amount

    def transfer(self, sender, recipient, amount):
        if self.balances[sender] >= amount:
            self.balances[sender] -= amount
            self.balances[recipient] += amount
            return True
        return False

class KnowledgeRegistryContract:
    def __init__(self):
        self.registered_knowledge = {}
        self.callback_targets = []

    def register_knowledge(self, knowledge: Dict[str, Any]):
        knowledge_id = knowledge["knowledge_id"]
        if 'usage_count' not in knowledge:
            knowledge['usage_count'] = 0
        self.registered_knowledge[knowledge_id] = knowledge
        for target in self.callback_targets:
            target.handle_knowledge_registration(knowledge)

    def add_callback_target(self, target):
        self.callback_targets.append(target)

class IndexUpdaterCallback:
    def __init__(self, librarian: Librarian):
        self.librarian = librarian

    def handle_knowledge_registration(self, knowledge: Dict[str, Any]):
        self.librarian.add_index(knowledge["knowledge_id"], knowledge)
        vprint(f"IndexUpdaterCallback: Added knowledge {knowledge['knowledge_id']} to Librarian.")

class KnowledgeProvider(mesa.Agent):
    def __init__(self, unique_id: int, model: mesa.Model, provider_id: str):
        super().__init__(unique_id, model)
        self.provider_id = provider_id
        self.all_lemmas = list(wordnet.all_lemma_names())
        self.batch_balance = 1000
        self.knowledge_tokens = {}

    def upload_knowledge(self, index: str, embedding_model: str) -> Dict[str, Any]:
        topic = random.choice(self.all_lemmas)
        content = fake.paragraph(nb_sentences=random.randint(7, 10), variable_nb_sentences=True)
        knowledge_id = hashlib.sha256(f"{self.provider_id}_{index}_{topic}".encode()).hexdigest()
        knowledge = {
            "provider_id": self.provider_id,
            "knowledge_id": knowledge_id,
            "index": index,
            "embedding_model": embedding_model,
            "topic": topic,
            "content": content,
            "creation_time": time.time(),
            "value": random.randint(10, 100) * config.knowledge_value_multiplier,
            "usage_count": 0,
            "rating": 0
        }
        self.knowledge_tokens[knowledge_id] = KnowledgeSupportToken(knowledge_id, self.provider_id)
        return knowledge

class Validator(mesa.Agent):
    def __init__(self, unique_id, model, validator_id, dkn, librarian):
        super().__init__(unique_id, model)
        self.validator_id = validator_id
        self.dkn = dkn
        self.librarian = librarian
        self.batch_balance = 1000

    def fetch_context(self, topic: str) -> Tuple[str, List[str]]:
        web_context = f"Web context about {topic}"
        librarian_contexts = [result[1]['content'] for result in self.librarian.search(topic)[:3]]
        return web_context, librarian_contexts

    def use_llm_to_compare(self, web_context: str, librarian_context: str) -> bool:
        return web_context in librarian_context

    def validate(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        topic = knowledge['topic']
        web_context, librarian_contexts = self.fetch_context(topic)
        all_comparisons = [self.use_llm_to_compare(web_context, lib_context) for lib_context in librarian_contexts]
        is_factual = all(all_comparisons)
        result_hash = hashlib.sha256(knowledge['content'].encode()).hexdigest()
        signature = "signature_placeholder"
        encrypted_result = "encrypted_result_placeholder"
        return {
            "factual": is_factual,
            "hash": result_hash,
            "signature": signature,
            "encrypted_result": encrypted_result
        }

    def compute(self, task):
        if task['type'] == 'validate':
            return self.validate(task['knowledge'])
        return 0

    def verify(self, result):
        return result["factual"]

class KnowledgeSupporter(mesa.Agent):
    def __init__(self, unique_id, model, supporter_id):
        super().__init__(unique_id, model)
        self.supporter_id = supporter_id
        self.batch_balance = 1000
        self.support_tokens = {}

    def buy_support_tokens(self, knowledge_id: str, amount: int, batch_token: BatchToken, provider: KnowledgeProvider):
        cost = amount * batch_token.economic_model.token_price
        if self.batch_balance >= cost:
            if batch_token.transfer(self.supporter_id, provider.provider_id, cost):
                provider.knowledge_tokens[knowledge_id].mint(self.supporter_id, amount)
                if knowledge_id not in self.support_tokens:
                    self.support_tokens[knowledge_id] = 0
                self.support_tokens[knowledge_id] += amount
                self.batch_balance -= cost
                vprint(f"Debug: {self.supporter_id} bought {amount} support tokens for knowledge {knowledge_id[:8]} at cost {cost:.2f}")
                return True
        vprint(f"Debug: {self.supporter_id} failed to buy support tokens for knowledge {knowledge_id[:8]}")
        return False

class KnowledgeSeeker(mesa.Agent):
    def __init__(self, unique_id, model, seeker_id):
        super().__init__(unique_id, model)
        self.seeker_id = seeker_id
        self.all_lemmas = list(wordnet.all_lemma_names())
        self.batch_balance = 1000

    def make_query(self) -> str:
        action = random.choice(["What is", "How does", "Why is", "Explain"])
        topic = random.choice(self.all_lemmas)
        query = f"{action} {topic}?"
        vprint(f"Debug: Generated query: {query}")
        return query

class QueryContract:
    def __init__(self):
        self.fee_structure = {
            "base_fee": config.query_fee,
            "priority_fee": config.query_fee * 2,
            "data_fee": config.query_fee * 3
        }

    def calculate_fees(self) -> float:
        return sum(self.fee_structure.values())

class HollowDB:
    def __init__(self):
        self.storage = {}

    def store_knowledge(self, knowledge_id: str, knowledge: Dict[str, Any]):
        self.storage[knowledge_id] = knowledge

class Sequencer:
    def __init__(self):
        self.transactions = []

    def sequence_transaction(self, transaction: Dict[str, Any]):
        self.transactions.append(transaction)

class MetricsTracker:
    def __init__(self):
        self.metrics = defaultdict(list)
    def add_metric(self, metric_name, value):
        self.metrics[metric_name].append(value)
    def get_latest(self, metric_name):
        return self.metrics[metric_name][-1] if self.metrics[metric_name] else None
    def write_to_csv(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(list(self.metrics.keys()))
            # Write data
            for time_step in range(len(next(iter(self.metrics.values())))):
                row = [self.metrics[metric][time_step] if time_step < len(self.metrics[metric]) else '' for metric in self.metrics]
                writer.writerow(row)

# Initialize core components
def initialize_core_components():
    economic_model = EconomicModel(1000000, 1.0)
    batch_token = BatchToken(1000000, economic_model)
    knowledge_registry = KnowledgeRegistryContract()
    query_contract = QueryContract()
    hollowdb = HollowDB()
    sequencer = Sequencer()
    librarian = Librarian()
    dkn = DKN(knowledge_registry)
    synthetic_data_generator = SyntheticDataGenerator(librarian)
    dria_l2 = DriaL2(batch_token)
    index_updater_callback = IndexUpdaterCallback(librarian)
    knowledge_registry.add_callback_target(index_updater_callback)
    metrics = MetricsTracker()

    return {
        "economic_model": economic_model,
        "batch_token": batch_token,
        "knowledge_registry": knowledge_registry,
        "query_contract": query_contract,
        "hollowdb": hollowdb,
        "sequencer": sequencer,
        "librarian": librarian,
        "dkn": dkn,
        "synthetic_data_generator": synthetic_data_generator,
        "dria_l2": dria_l2,
        "metrics": metrics
    }

# Create participants
def create_participants(num_providers, num_validators, num_supporters, num_seekers, model, librarian, dkn):
    providers = [KnowledgeProvider(i, model, f"provider_{i}") for i in range(num_providers)]
    validators = [Validator(num_providers + i, model, f"validator_{i}", dkn, librarian) for i in range(num_validators)]
    supporters = [KnowledgeSupporter(num_providers + num_validators + i, model, f"supporter_{i}") for i in range(num_supporters)]
    seekers = [KnowledgeSeeker(num_providers + num_validators + num_supporters + i, model, f"seeker_{i}") for i in range(num_seekers)]
    for validator in validators:
        dkn.add_node(validator)
    return providers, validators, supporters, seekers

# Allocate initial balances
def allocate_initial_balances(batch_token, providers, validators, supporters, seekers):
    for provider in providers:
        batch_token.allocate_initial_balance(provider.provider_id, provider.batch_balance)
    for validator in validators:
        batch_token.allocate_initial_balance(validator.validator_id, validator.batch_balance)
    for supporter in supporters:
        batch_token.allocate_initial_balance(supporter.supporter_id, supporter.batch_balance)
    for seeker in seekers:
        batch_token.allocate_initial_balance(seeker.seeker_id, seeker.batch_balance)

# Day start actions
def perform_day_start_actions(day, batch_token, economic_model):
    vprint(f"\nDay {day}")
    vprint(f"BATCH Token supply: {batch_token.total_supply:.0f}")
    vprint(f"BATCH Token price: {economic_model.token_price:.4f}")

# Provider uploads knowledge
def provider_upload_knowledge(providers, validators, dkn, batch_token, dria_l2, knowledge_registry, hollowdb, librarian):
    total_validations = 0
    successful_validations = 0
    for provider in providers:
        knowledge = provider.upload_knowledge(f"index_{provider.provider_id}", "embedding_model_1")
        transaction = {
            "type": "knowledge_upload",
            "knowledge_id": knowledge["knowledge_id"],
            "provider_id": provider.provider_id,
            "sender": provider.provider_id
        }
        if dria_l2.process_transaction(transaction):
            validation_results = [validator.compute({"type": "validate", "knowledge": knowledge}) for validator in validators]
            aggregated_result = dkn.aggregate_results([result["factual"] for result in validation_results])
            if dkn.verify_result(aggregated_result):
                knowledge_registry.register_knowledge(knowledge)
                hollowdb.store_knowledge(knowledge["knowledge_id"], knowledge)
                librarian.add_index(knowledge["knowledge_id"], knowledge)
                vprint(f"Knowledge '{knowledge['topic']}' (ID: {knowledge['knowledge_id'][:8]}) validated successfully.")
                successful_validations += 1
                reward = knowledge['value'] * config.provider_reward_percentage
                batch_token.mint(provider.provider_id, reward)
                provider.batch_balance += reward
                vprint(f"Provider {provider.provider_id} rewarded {reward:.2f} BATCH tokens.")
                for validator in validators:
                    validator_reward = knowledge['value'] * config.validator_reward_percentage / len(validators)
                    batch_token.mint(validator.validator_id, validator_reward)
                    validator.batch_balance += validator_reward
                    vprint(f"Validator {validator.validator_id} rewarded {validator_reward:.2f} BATCH tokens.")
            else:
                vprint(f"Knowledge '{knowledge['topic']}' (ID: {knowledge['knowledge_id'][:8]}) validation failed.")
            total_validations += 1
    return total_validations, successful_validations

# Process synthetic data
def process_synthetic_data(librarian, synthetic_data_generator, dkn, validators, dria_l2, knowledge_registry, hollowdb):
    successful_validations = 0
    total_validations = 0
    if random.random() < 0.2:  # 20% chance of generating synthetic data
        topic = random.choice(list(librarian.context_tree.keys())) if librarian.context_tree else "default_topic"
        bias_config = {"bias_type": random.choice(["positive", "negative", "neutral"])}
        synthetic_data = synthetic_data_generator.generate_data(topic, bias_config)
        vprint(f"Generated synthetic data for topic: {topic}")
        synthetic_knowledge = {
            "provider_id": "synthetic_provider",
            "knowledge_id": hashlib.sha256(f"synthetic_{topic}".encode()).hexdigest(),
            "index": "synthetic_index",
            "embedding_model": "synthetic_model",
            "topic": topic,
            "content": synthetic_data["content"],
            "creation_time": synthetic_data["creation_time"],
            "value": synthetic_data["value"],
            "usage_count": 0,
            "rating": 0
        }
        if dria_l2.process_transaction(
                {"type": "knowledge_upload", "knowledge_id": synthetic_knowledge["knowledge_id"], "provider_id": "synthetic_provider", "sender": "synthetic_provider"}):
            validation_results = [validator.compute({"type": "validate", "knowledge": synthetic_knowledge}) for validator in validators]
            aggregated_result = dkn.aggregate_results([result["factual"] for result in validation_results])
            if dkn.verify_result(aggregated_result):
                knowledge_registry.register_knowledge(synthetic_knowledge)
                hollowdb.store_knowledge(synthetic_knowledge["knowledge_id"], synthetic_knowledge)
                librarian.add_index(synthetic_knowledge["knowledge_id"], synthetic_knowledge)
                vprint(f"Synthetic knowledge '{synthetic_knowledge['topic']}' (ID: {synthetic_knowledge['knowledge_id'][:8]}) validated successfully.")
                successful_validations += 1
            else:
                vprint(f"Synthetic knowledge '{synthetic_knowledge['topic']}' (ID: {synthetic_knowledge['knowledge_id'][:8]}) validation failed.")
            total_validations += 1
    return successful_validations, total_validations

# Seeker makes queries
def seeker_make_queries(seekers, dria_l2, sequencer, query_contract, librarian, batch_token):
    queries_processed = 0
    total_fees = 0
    for seeker in seekers:
        query = seeker.make_query()
        transaction = {
            "type": "query",
            "seeker_id": seeker.seeker_id,
            "query": query,
            "sender": seeker.seeker_id
        }
        
        if dria_l2.process_transaction(transaction):
            sequencer.sequence_transaction(transaction)
            query_fee = query_contract.calculate_fees()
            if seeker.batch_balance >= query_fee:
                processed_query = librarian.search(query)
                if batch_token.transfer(seeker.seeker_id, "fee_pool", query_fee):
                    seeker.batch_balance -= query_fee
                    vprint(f"Query processed for {seeker.seeker_id}: {processed_query[:2]}")  # Show only top 2 results
                    for knowledge_id, knowledge in processed_query[:2]:
                        knowledge['usage_count'] += 1
                    queries_processed += 1
                    total_fees += query_fee
                else:
                    vprint(f"Query fee transfer failed for {seeker.seeker_id}")
    return queries_processed, total_fees

# Update knowledge values and process rewards
def update_knowledge_values_and_process_rewards(hollowdb, providers, batch_token, simulated_time):
    rewards = {'provider': 0, 'supporter': 0}
    for knowledge_id, knowledge in hollowdb.storage.items():
        age = (simulated_time - knowledge['creation_time']) / 86400  # age in days
        if age > config.knowledge_decay_threshold:
            knowledge['value'] *= (1 - config.knowledge_decay_rate) ** (age - config.knowledge_decay_threshold)
        provider = next((p for p in providers if p.provider_id == knowledge['provider_id']), None)
        if provider:
            support_token = provider.knowledge_tokens.get(knowledge_id)
            if support_token:
                total_support = sum(support_token.balances.values())
                if total_support > 0:
                    supporter_reward = knowledge['value'] * config.supporter_reward_percentage * (knowledge['usage_count'] / 10)
                    for supporter_id, balance in support_token.balances.items():
                        reward = supporter_reward * (balance / total_support)
                        batch_token.mint(supporter_id, reward)
                        vprint(f"Supporter {supporter_id} received {reward:.2f} BATCH tokens for supporting knowledge {knowledge_id[:8]}")
                        rewards['supporter'] += reward
            provider_reward = knowledge['value'] * config.provider_reward_percentage * (knowledge['usage_count'] / 10)
            batch_token.mint(provider.provider_id, provider_reward)
            rewards['provider'] += provider_reward
    return rewards
# Economic model update
def economic_model_update(seekers, supporters, economic_model):
    total_demand = sum(seeker.batch_balance for seeker in seekers) + sum(supporter.batch_balance for supporter in supporters)
    economic_model.update(total_demand)

# Simulation summary
def simulation_summary(batch_token, economic_model, successful_validations, total_validations, validators, providers, supporters, seekers):
    print("\nSimulation Complete")
    print(f"Total successful validations: {successful_validations} / {total_validations}")
    print(f"Final BATCH Token supply: {batch_token.total_supply:.0f}")
    print(f"Final BATCH Token price: {economic_model.token_price:.4f}")
    for provider in providers:
        print(f"Provider {provider.provider_id} final BATCH balance: {provider.batch_balance:.2f}")
    for validator in validators:
        print(f"Validator {validator.validator_id} final BATCH balance: {validator.batch_balance:.2f}")
    for supporter in supporters:
        print(f"Supporter {supporter.supporter_id} final BATCH balance: {supporter.batch_balance:.2f}")
    for seeker in seekers:
        print(f"Seeker {seeker.seeker_id} final BATCH balance: {seeker.batch_balance:.2f}")

# Model Class for Mesa
class KnowledgeModel(mesa.Model):
    def __init__(self, num_providers, num_validators, num_supporters, num_seekers):
        self.num_providers = num_providers
        self.num_validators = num_validators
        self.num_supporters = num_supporters
        self.num_seekers = num_seekers
        self.schedule = mesa.time.RandomActivation(self)

        # Initialize core components
        components = initialize_core_components()
        self.economic_model = components['economic_model']
        self.batch_token = components['batch_token']
        self.knowledge_registry = components['knowledge_registry']
        self.query_contract = components['query_contract']
        self.hollowdb = components['hollowdb']
        self.sequencer = components['sequencer']
        self.librarian = components['librarian']
        self.dkn = components['dkn']
        self.synthetic_data_generator = components['synthetic_data_generator']
        self.dria_l2 = components['dria_l2']
        self.metrics = components['metrics']

        # Create participants
        self.providers, self.validators, self.supporters, self.seekers = create_participants(
            self.num_providers, self.num_validators, self.num_supporters, self.num_seekers, self, self.librarian, self.dkn
        )


        # Add agents to schedule
        for provider in self.providers:
            self.schedule.add(provider)
        for validator in self.validators:
            self.schedule.add(validator)
        for supporter in self.supporters:
            self.schedule.add(supporter)
        for seeker in self.seekers:
            self.schedule.add(seeker)

        # Allocate initial balances
        allocate_initial_balances(self.batch_token, self.providers, self.validators, self.supporters, self.seekers)

        # Initialize simulation variables
        self.day = 0
        self.time_step = 0
        self.simulated_time = 0
        self.total_validations = 0
        self.successful_validations = 0

    def step(self):
        if int(self.simulated_time / 86400) > self.day:
            self.day += 1
            perform_day_start_actions(self.day, self.batch_token, self.economic_model)


        self.metrics.add_metric('Time_Step', self.time_step)
        self.metrics.add_metric('Simulated_Time', self.simulated_time)
        self.metrics.add_metric('Day', self.day)
        self.metrics.add_metric('BATCH_Token_Supply', self.batch_token.total_supply)
        self.metrics.add_metric('BATCH_Token_Price', self.economic_model.token_price)
        self.metrics.add_metric('Total_Demand', self.economic_model.demand)
        self.metrics.add_metric('Liquidity', self.economic_model.liquidity)
        self.metrics.add_metric('Knowledge_Count', len(self.hollowdb.storage))
        self.metrics.add_metric('Total_Queries', len(self.sequencer.transactions))

        provider_balances = [p.batch_balance for p in self.providers]
        validator_balances = [v.batch_balance for v in self.validators]
        supporter_balances = [s.batch_balance for s in self.supporters]
        seeker_balances = [s.batch_balance for s in self.seekers]

        self.metrics.add_metric('Avg_Provider_Balance', sum(provider_balances) / len(provider_balances))
        self.metrics.add_metric('Avg_Validator_Balance', sum(validator_balances) / len(validator_balances))
        self.metrics.add_metric('Avg_Supporter_Balance', sum(supporter_balances) / len(supporter_balances))
        self.metrics.add_metric('Avg_Seeker_Balance', sum(seeker_balances) / len(seeker_balances))

        # Providers upload knowledge
        valid, success = provider_upload_knowledge(
            self.providers, self.validators, self.dkn, self.batch_token, self.dria_l2,
            self.knowledge_registry, self.hollowdb, self.librarian)

        self.total_validations += valid
        self.successful_validations += success
        self.metrics.add_metric('Knowledge_Uploads', valid)
        self.metrics.add_metric('Successful_Validations_Step', success)

        # Process synthetic data
        synthetic_valid, synthetic_success = process_synthetic_data(
            self.librarian, self.synthetic_data_generator, self.dkn, self.validators,
            self.dria_l2, self.knowledge_registry, self.hollowdb)


        self.total_validations += synthetic_valid
        self.successful_validations += synthetic_success
        self.metrics.add_metric('Synthetic_Data_Generated', synthetic_valid)
        self.metrics.add_metric('Synthetic_Data_Validated', synthetic_success)

        # Seekers make queries
        queries_processed, query_fees = seeker_make_queries(self.seekers, self.dria_l2, self.sequencer, self.query_contract, self.librarian, self.batch_token)
        self.metrics.add_metric('Queries_Processed', queries_processed)
        self.metrics.add_metric('Query_Fees_Collected', query_fees) 

        # Update knowledge values and process rewards
        rewards = update_knowledge_values_and_process_rewards(self.hollowdb, self.providers, self.batch_token, self.simulated_time)
        self.metrics.add_metric('Provider_Rewards', rewards['provider'])
        self.metrics.add_metric('Supporter_Rewards', rewards['supporter'])
        # Update economic model
        economic_model_update(self.seekers, self.supporters, self.economic_model)
        self.metrics.add_metric('Total_Validations', self.total_validations)
        self.metrics.add_metric('Successful_Validations', self.successful_validations)
        # Advance time
        self.simulated_time += 21600
        self.schedule.step()

    def run(self, n):
        for _ in range(n):
            self.step()

if __name__ == "__main__":
    try:
        iters = 1000
        p = 10
        v = 8
        s = 34
        e = 23

        model = KnowledgeModel(p, v, s, e)
        model.run(iters) 
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
    finally:
        simulation_summary(
            model.batch_token, 
            model.economic_model, 
            model.successful_validations, 
            model.total_validations, 
            model.validators, 
            model.providers, 
            model.supporters, 
            model.seekers
        )
    
    sim_id = str(f'data/iters_{iters}.csv')
    model.metrics.write_to_csv(sim_id)
