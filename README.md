# BLM5027 Finals Project - Reinforcement Learning with Container Sorter
Bu projede, Q-Learning algoritmasını kullanarak farklı boyutlarda bir yığın konteyneri çıkış önceliklerini göz önünde bulundurarak sıralı bir şekilde üç adet limana istifleyebilecek bir ajan eğiteceğiz.

## Proje Detayları
Bu projede, bir kargo alanındaki konteynerleri alıp çıkarılacakları sıraya, boyutlarına ve özelliklerine göre limanlara taşıyacak bir düzenleyici (Sorter) tasarlanmıştır. Konteynerler, kargo alanından sırayla çıkarılmalıdır ve hepsinin sırasından bağımsız bir çıkış önceliği bulunmaktadır. 

Düzenleyicinin amacı, bu konteynerleri limanlara dizerken daha önce çıkarılması gereken konteynerleri daha yukarı ve daha sonra çıkarılması gereken konteynerleri daha aşağıya yerleştirmektir. Eğer ki önceliği olan bir konteyner altta kalırsa, onu çıkarmak için üstündeki konteynerleri hareket ettirmesi gerekmektedir ve bu da bulunan kısıtlı alandan ötürü çok büyük bir zaman kaybıdır. 

Projenin güncel hâlinde konteynerlere iki yeni özellik eklenmiştir. Bunlardan ilki konteyner boyutudur. Her konteyner küçük (S), orta (M) veya büyük (L) boyutlarından birine sahiptir. İstifleme sırasında daha büyük bir konteyner, daha küçük bir konteynerin üzerine yerleştirilemez. Bu sebepten ötürü bir konteyner yalnızca kendisiyle aynı boyutta veya kendisinden büyük bir konteynerin üzerine konulabilir. İkinci yeni özellik ise bazı konteynerlerin içerisinde diğer konteynerler ile birlikte bulundurulmaması gereken zehirli kimyasal maddelerin olmasıdır. Bu konteynerler toksik olarak işaretlenmiştir ve düzenleme tamamlandığında bu konteynerlerin kendilerine özgün ayrı bir limanda bulunması beklenmektedir. 

Güncel sistemde toplam dört liman bulunmaktadır:

* Birinci liman
* İkinci liman
* Geçici liman
* Toksik Madde limanı

Birinci ve ikinci liman, normal konteynerlerin yerleştirilmesi gereken limanlardır. Geçici liman, konteynerlerin yerini değiştirirken ara depolama alanı olarak kullanılabilir ancak düzenlemenin başarılı sayılabilmesi için işlem sonunda geçici limanın boş olması gerekmektedir. Toksik madde limanı ise toksik madde içeren konteynerlerin ayrıştırılması için eklenmiştir.

Limanların boyutları, kargodaki bütün konteynerleri dizebilmeye yetecek kadar olmalıdır. Bu versiyonda eklenen özelliklerden ötürü modele yardımcı olmak adına limanların kapasitesini arttırarak toplam konteyner sayısına eşitledim. Aynı zamanda da geçici limanın boyutu n adet konteyner için ⌊(n+1)/2⌋ olarak değiştirildi.

Düzenleyici, her adımda 4 + 12 = 16 adet farklı eylemden birini gerçekleştirebilir:

- 0-3: Kargo alanından Limana konteyner yerleştirme (0: Birinci limana yerleştir, 1: İkinci limana yerleştir, 2: Geçici limana yerleştir, 3: Toksik madde limanına yerleştir)
- 4-15: Limanlar arası konteyner taşıma (4-6: Birinci limandan ikinci/geçici/toksik limana taşı, 7-9: İkinci limandan birinci/geçici/toksik limana taşı, 10-12: Geçici limandan birinci/ikinci/toksik limana taşı, 13-15: Toksik limandan birinci/ikinci/geçici limana taşı)

```
def can_place_to_port(container, port_id): ### If this container can legally be placed on this port
        if len(Sorter.ports[port_id]) >= Sorter.port_limit(port_id):
            return False
        elif not Sorter.can_stack_on_port(container, port_id): ###
            return False
        return True
        
def place_to_port(port_id):
        if len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], port_id):
            container = Sorter.cargo.pop(0)
            Sorter.ports[port_id].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move
    
    def place_to_temp_port():
        if len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], 2):
            container = Sorter.cargo.pop(0)
            Sorter.ports[2].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move

    def place_to_toxic_port():
        if len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], 3):
            container = Sorter.cargo.pop(0)
            Sorter.ports[3].append(container) ### Takes the first element of cargo and places it into the port
            return -1
        else:
            return -10 ### Illegal move
    
    def move_from_port(source_id, target_id):
        if len(Sorter.ports[source_id]) > 0 and Sorter.can_place_to_port(Sorter.ports[source_id][-1], target_id): 
            container = Sorter.ports[source_id].pop(-1)
            Sorter.ports[target_id].append(container) ### Takes the last element of a port and moves it to another port

            return -1
            # if target_id == 2:
            #     return -2 ### Discourage the temporary port
            # else:
            #     return -1
        else:
            return -10 ### Illegal move
```

Limanlar arasında konteyner taşınırken sadece en üstte bulunan konteyner hareket ettirilebiliyor. Bu eylemlerin her biri zaman kaybına sebep olduğundan ötürü -1 ve imkansız oldukları durumlarda denenirlerse o zaman -10 puanlık bir cezaya sebep olurlar. Aynı zamanda her bir adımda düzenleyici, eylem gerçekleştirdikten sonra konteynerlerin düzeni üzerinden de değerlendirilir:

- Kargo alanında bulunan her bir konteyner başına -1 puan (Kargo alanını boşaltmayı ödüllendirmek adına)
- Eğer bütün limanlardaki konteynerler düzenli bir şekilde yerleştirilmiş ve geçici liman boş bırakıldıysa +1000 puan (Düzenleyicininn görevi tamamlanmıştır.)

```
def container_check():
    reward = 0
    
    ### Penalize keeping cargo in the queue (encourage placing)
    reward -= len(Sorter.cargo)
    
    ### If all the cargo are placed correctly
    if len(Sorter.cargo) == 0 and len(Sorter.ports[2]) == 0:
        if False not in [Sorter.is_sorted(n) for n in range(3)]:
            reward += 1000
    return reward
```

## Model Yapısı
Bu modelin bir önceki versiyonunda durum uzayını yapabildiğimizce küçülterek eğitim süremizi ve eğitim sırasında öğrendiğimiz durum oranını yükseltmeye çalışmıştık:
> 4 konteyner = 13,005  
> 5 konteyner = 63,426  
> 6 konteyner = 124,579  
> 7 konteyner = 753,768  
> 8 konteyner = 1,254,825  

Fakat yeni eklediğimiz özelliklerden dolayı modelimiz daha da karışık bir hale gelmiştir ve önceki modelde uyguladığımız optimizasyonlara rağmen durum uzayımız katlarca büyümüştür:
> 4 konteyner = 275,346,465,625  
> 5 konteyner = 2,429,362,434,991   
> 6 konteyner = 10,369,025,507,125   
> 7 konteyner = 47,185,972,290,787  
> 8 konteyner = 136,818,247,206,193  

```
    def container_size(container): ### The size value of a container
        return Sorter.container_sizes[container]

    def is_toxic(container): ### Whether a container has toxic material
        return container in Sorter.toxic_containers

    def port_limit(n): ### The capacity limit of a port
        return [Sorter.port_capacity, Sorter.port_capacity, Sorter.temp_port_capacity, Sorter.toxic_port_capacity][n]

    def is_sorted(n): ### If a port is arranged correctly (lower priority above higher priority)
        for i in range(len(Sorter.ports[n]) - 1):
            if Sorter.ports[n][i] < Sorter.ports[n][i + 1]:
                return False
        return True

    def is_size_sorted(n): ### If a port is arranged correctly by size (same or smaller above larger)
        for i in range(len(Sorter.ports[n]) - 1):
            if Sorter.container_size(Sorter.ports[n][i]) < Sorter.container_size(Sorter.ports[n][i + 1]):
                return False
        return True

    def is_toxic_sorted(n): ### If toxic containers are kept away from regular ports
        for container in Sorter.ports[n]:
            if n == 3 and not Sorter.is_toxic(container):
                return False
            if n != 3 and n != 2 and Sorter.is_toxic(container):
                return False
        return True

    def can_stack_on_port(container, port_id): ### If this container can be stacked on this port by size
        if len(Sorter.ports[port_id]) == 0:
            return True

        top_box = Sorter.ports[port_id][-1]
        return Sorter.container_size(container) <= Sorter.container_size(top_box)

    def can_place_to_port(container, port_id): ### If this container can legally be placed on this port
        if len(Sorter.ports[port_id]) >= Sorter.port_limit(port_id):
            return False
        elif not Sorter.can_stack_on_port(container, port_id): ###
            return False
        return True

    def incoming_state(): ### The current state value of the incoming container
        if len(Sorter.cargo) == 0:
            return Sorter.number_of_containers * 3 * 2

        container = Sorter.cargo[0]
        size = Sorter.container_size(container)
        toxic_flag = int(Sorter.is_toxic(container))

        return (container * 3 + size) * 2 + toxic_flag

    def port_state(n): ### The current state value of a port
        port = Sorter.ports[n]
        if len(port) == 0:
            return 0

        height = len(port)
        top_box = port[-1]
        top_size = Sorter.container_size(top_box)
        top_toxic_flag = int(Sorter.is_toxic(top_box))
        sorted_flag = int(Sorter.is_sorted(n))
        stack_flag = 1

        if len(Sorter.cargo) > 0:
            stack_flag = int(Sorter.can_stack_on_port(Sorter.cargo[0], n))

        return 1 + (
            (((((height - 1) * Sorter.number_of_containers + top_box) * 3 + top_size) * 2 + sorted_flag) * 2 + stack_flag) * 2 + top_toxic_flag
        )

    def get_current_state(): ### Find the current state of the system
        incoming = Sorter.incoming_state()

        main_port_states = 1 + Sorter.number_of_containers * Sorter.port_capacity * 3 * 2 * 2 * 2
        temp_port_states = 1 + Sorter.number_of_containers * Sorter.temp_port_capacity * 3 * 2 * 2 * 2
        toxic_port_states = 1 + Sorter.number_of_containers * Sorter.toxic_port_capacity * 3 * 2 * 2 * 2

        port_1_state = Sorter.port_state(0)
        port_2_state = Sorter.port_state(1)
        temp_state = Sorter.port_state(2)
        toxic_state = Sorter.port_state(3)

        state = incoming
        state = state * main_port_states + port_1_state
        state = state * main_port_states + port_2_state
        state = state * temp_port_states + temp_state
        state = state * toxic_port_states + toxic_state

        return state
```

Bu yüzden de 0'larla dolu bir durum matrisi kullanmaktansa sadece görülmüş ve öğrenilmiş durumların bulunduğu bir dictionary kullanma kararı verdim. Bu dictionary'de bulunmayan bir durumla karşılaşıldığında da model rastgele legal bir eylem yaparak ilerlemeye çalışacaktır.

```
    def get_q_values(state): ### Get the Q-values for a state
        if state not in Sorter.q_table:
            Sorter.q_table[state] = np.zeros(Sorter.num_of_actions)
        return Sorter.q_table[state]
```
```
    def step(learn = False):
        old_state = Sorter.get_current_state()
        no_actions_available = old_state not in Sorter.q_table
        q_values = Sorter.get_q_values(old_state)
        no_actions_available = no_actions_available or not np.any(q_values != 0)

        if no_actions_available:               ### If there is no learned action for this state
            reward = 0
            attempt_count = 0
            attempt_reward = -10
            while attempt_reward == -10:
                Sorter.action = rnd.randrange(Sorter.num_of_actions)
                attempt_reward = Sorter.act()
                reward += attempt_reward
                if attempt_reward == -10:
                    attempt_count += 1
            reward += 10 * attempt_count       ### Offset the illegal random attempts
        else:
            if rnd.uniform(0, 1) < Sorter.epsilon:  ### Explore
                Sorter.action = rnd.randrange(Sorter.num_of_actions)
            else:                                   ### Exploit
                Sorter.action = np.argmax(q_values)
```


Q-Learning güncellemesi standart formülle yapılmaktadır:
Q(s, a) = (1 - _α_) \* Q(s, a) + _α_ \* (_r_ + _γ_ \* max(Q(s')))

s : Şu anki durum\
a : Şu anki eylem\
s': Bir sonraki durum

_α_ : learning rate (öğrenme oranı) [0.2]\
_γ_ : discount factor (indirim faktörü) [0.95]\
_r_ : reward (bu durumdaki alınan ödül)

```
def update_q_table(old_state, old_value, next_value, reward):
        Sorter.q_table[old_state, Sorter.action] = (1 - Sorter.learning_rate) * old_value + Sorter.learning_rate * (reward + Sorter.discount_factor * next_value)
```

Eylem seçimi için Epsilon Greedy algoritmasından yararlanacağız. Bu algoritmada verilen bir _ε_ değerine oranla model ya öğrendiği bilgiler arasından en optimal olanı yapar ya da rastgele eylemler gerçekleştirerek yeni bilgi edinmeye çalışır.

_ε_ : Epsilon [0.95 -> 0.01, Decay rate = 0.0025%]

```
if rnd.uniform(0, 1) < Sorter.epsilon:
        Sorter.action = rnd.randrange(Sorter.num_of_actions)
else:
        Sorter.action = np.argmax(Sorter.q_table[old_state])
```


## Eğitim Süreci ve Sonuçlar
Eğitim süreci sırasında yaşanan en büyük problem, yeni modelin kompleksitelerinden dolayı eğitim sürecinin uzamasıydı. Olabilecek daha fazla muhtemel durum olduğundan dolayı eski modele göre daha fazla episode (bölüm) eğitmek gerekiyordu ve bu eğitim süreçleri de çok daha uzun sürüyordu. Bununla birlikte de eski modelde de karşılaşılan hamle tekrarlama problemi tekrardan ortaya çıkmaya başlamıştı.
