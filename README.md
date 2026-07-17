# BLM5027 Finals Project - Reinforcement Learning with Container Sorter
Bu projede, Q-Learning algoritmasını kullanarak farklı boyutlardaki konteynerleri çıkış önceliklerini göz önünde bulundurarak uygun limanlara sıralı bir şekilde istifleyebilecek bir ajan eğitilmektedir.

## Proje Detayları
Bu projede, bir kargo alanındaki konteynerleri alıp çıkarılacakları sıraya, boyutlarına ve özelliklerine göre limanlara taşıyacak bir düzenleyici (Sorter) tasarlanmıştır. Konteynerler, kargo alanından sırayla alınmalıdır; ancak her konteynerin bu sıradan bağımsız bir çıkış önceliği bulunmaktadır. Düzenleyicinin amacı, konteynerleri limanlara dizerken daha önce çıkarılması gereken konteynerleri daha yukarıya, daha sonra çıkarılması gereken konteynerleri ise daha aşağıya yerleştirmektir. Eğer öncelikli bir konteyner altta kalırsa, onu çıkarmak için üstündeki konteynerlerin hareket ettirilmesi gerekir. Bu da sınırlı alandan dolayı önemli bir zaman kaybına sebep olur. Projenin güncel hâlinde konteynerlere iki yeni özellik eklenmiştir. Bunlardan ilki konteyner boyutudur. Her konteyner küçük (S), orta (M) veya büyük (L) boyutlarından birine sahiptir. İstifleme sırasında daha büyük bir konteyner, daha küçük bir konteynerin üzerine yerleştirilemez. Bu sebeple bir konteyner yalnızca kendisiyle aynı boyutta veya kendisinden büyük bir konteynerin üzerine konulabilir. İkinci yeni özellik ise bazı konteynerlerin içerisinde diğer konteynerlerle birlikte bulundurulmaması gereken zehirli kimyasal maddelerin olmasıdır. Bu konteynerler toksik olarak işaretlenmiştir ve düzenleme tamamlandığında kendilerine ayrılmış ayrı bir limanda bulunmaları beklenmektedir. 

Güncel sistemde toplam dört liman bulunmaktadır:

* Birinci liman
* İkinci liman
* Geçici liman
* Toksik Madde Limanı

Birinci ve ikinci liman, normal konteynerlerin yerleştirilmesi gereken limanlardır. Geçici liman, konteynerlerin yerini değiştirirken ara depolama alanı olarak kullanılabilir; ancak düzenlemenin başarılı sayılabilmesi için işlem sonunda boş olması gerekmektedir. Toksik Madde Limanı ise toksik madde içeren konteynerlerin ayrıştırılması için eklenmiştir.

Liman kapasiteleri, kargodaki konteynerlerin düzenlenmesini mümkün kılacak şekilde belirlenmiştir. Bu versiyonda eklenen özelliklerden dolayı modele yardımcı olmak adına liman kapasiteleri artırılmıştır. Aynı zamanda geçici limanın boyutu n adet konteyner için ⌊(n+1)/2⌋ olarak değiştirilmiştir.

Düzenleyici, her adımda 4 + 12 = 16 adet farklı eylemden birini gerçekleştirebilir:

- 0-3: Kargo alanından limana konteyner yerleştirme (0: Birinci limana yerleştir, 1: İkinci limana yerleştir, 2: Geçici limana yerleştir, 3: Toksik madde limanına yerleştir)
- 4-15: Limanlar arası konteyner taşıma (4-6: Birinci limandan ikinci/geçici/toksik limana taşı, 7-9: İkinci limandan birinci/geçici/toksik limana taşı, 10-12: Geçici limandan birinci/ikinci/toksik limana taşı, 13-15: Toksik limandan birinci/ikinci/geçici limana taşı)

```
    def can_place_to_port(container, port_id): ### If this container can legally be placed on this port
        if len(Sorter.ports[port_id]) >= Sorter.port_limit(port_id):
            return False
        elif not Sorter.can_stack_on_port(container, port_id):
            return False
        elif not Sorter.is_toxic(container) and port_id == 3: ### Don't allow normal containers into toxic port
            return False
        return True

    ...
        
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

Limanlar arasında konteyner taşınırken sadece en üstte bulunan konteyner hareket ettirilebilir. Bu eylemlerin her biri zaman kaybına sebep olduğundan -1 puanlık cezaya sahiptir. İmkânsız oldukları durumlarda denenirlerse -10 puanlık daha büyük bir cezaya sebep olurlar. Aynı zamanda her adımda düzenleyici, eylem gerçekleştirdikten sonra konteynerlerin düzeni üzerinden de değerlendirilir:

- Kargo alanında bulunan her bir konteyner başına -1 puan (Kargo alanını boşaltmayı ödüllendirmek adına)
- Eğer bütün limanlardaki konteynerler düzenli bir şekilde yerleştirilmiş ve geçici liman boş bırakıldıysa +1000 puan (Düzenleyicinin görevi tamamlanmıştır.)

```
    def container_check():
        ### If all the cargo are placed correctly
        if len(Sorter.cargo) == 0 and len(Sorter.ports[2]) == 0:
            if False not in [Sorter.is_sorted(n) and Sorter.is_size_sorted(n) and Sorter.is_toxic_sorted(n) for n in range(4)]:
                return 1000
        return 0
```

## Model Yapısı
Bu modelin bir önceki versiyonunda durum uzayını mümkün olduğunca küçülterek eğitim süresini azaltmaya ve eğitim sırasında öğrenilen durum oranını yükseltmeye çalışmıştık:
> 4 konteyner = 13,005  
> 5 konteyner = 63,426  
> 6 konteyner = 124,579  
> 7 konteyner = 753,768  
> 8 konteyner = 1,254,825  

Fakat yeni eklenen özelliklerden dolayı model daha karmaşık bir hâle gelmiştir ve önceki modelde uygulanan optimizasyonlara rağmen durum uzayı katlarca büyümüştür:
> 4 konteyner = 275,346,465,625  
> 5 konteyner = 2,429,362,434,991   
> 6 konteyner = 10,369,025,507,125   
> 7 konteyner = 47,185,972,290,787  
> 8 konteyner = 136,818,247,206,193

Bu yüzden eklenen yeni durum modeli, konteynerlerin tam fiziksel konumunu doğrudan kodlamak yerine, karar verme açısından önemli olan aciliyet, yerleştirme uygunluğu, port doluluğu, öncelik ihlali ve en yakın çıkış konteynerinin konumu gibi özet özellikleri kullanmaktadır. Bu yaklaşım tam fiziksel temsil kadar ayrıntılı değildir; ancak durum uzayını daha anlamlı kategorilere ayırarak öğrenme sürecinde genelleme sağlamaktadır. Özellikle Port 1 ve Port 2’nin simetrik kabul edilmesi, modelin aynı yapısal durumu iki kez öğrenmesini engelleyerek eğitim verimliliğini artırmaktadır

```
     def all_containers():
        containers = list(Sorter.cargo)

        for port_id in range(Sorter.total_port_count):
            containers += Sorter.ports[port_id]

        return containers

    def incoming_state():
        if len(Sorter.cargo) == 0:
            return 0 ### Cargo empty

        container = Sorter.cargo[0]
        toxic_flag = int(Sorter.is_toxic(container))

        return 1 + toxic_flag * Sorter.number_of_containers + container

    def top_location():
        containers = Sorter.all_containers()

        if len(containers) == 0:
            return 0

        next_exit = min(containers)

        if next_exit in Sorter.cargo:
            return 0 ### Still in the cargo queue

        for port_id in range(Sorter.total_port_count):
            if next_exit in Sorter.ports[port_id]:
                depth = len(Sorter.ports[port_id]) - 1 - Sorter.ports[port_id].index(next_exit)

                if depth == 0:
                    return 1 ### On top of a port
                elif depth == 1:
                    return 2 ### Buried under one container
                return 3 ### Buried under two or more

        return 0

    def placement_relation(port_id): ### What placing the incoming container here would do to the exit order
        if len(Sorter.cargo) == 0 or len(Sorter.ports[port_id]) == 0:
            return 0 ### Nothing to compare against
        elif Sorter.cargo[0] < Sorter.ports[port_id][-1]:
            return 1 ### Safe, the incoming container leaves before the current top
        return 2 ### Buries a container that must leave earlier

    def top_is_next_exit(port_id): ### If the top container of this port must leave before everything else
        if len(Sorter.ports[port_id]) == 0:
            return 0

        return int(Sorter.ports[port_id][-1] == min(Sorter.all_containers()))

    def fullness_state(port_id):
        height = len(Sorter.ports[port_id])
        limit = Sorter.port_limit(port_id)

        if height == 0:
            return 0 ### Empty
        elif height == limit:
            return 3 ### Full
        elif height == limit - 1:
            return 2 ### One slot left
        return 1 ### Room to spare

    def can_place_cargo(port_id):
        return int(len(Sorter.cargo) > 0 and Sorter.can_place_to_port(Sorter.cargo[0], port_id))

    def main_port_state(port_id):
        can_place = Sorter.can_place_cargo(port_id)
        relation = Sorter.placement_relation(port_id)
        top_urgent = Sorter.top_is_next_exit(port_id)
        top_toxic = int(len(Sorter.ports[port_id]) > 0 and Sorter.is_toxic(Sorter.ports[port_id][-1]))
        fullness = Sorter.fullness_state(port_id)
        violation = int(not Sorter.is_sorted(port_id)) ### Wrong order

        return ((((can_place * 3 + relation) * 2 + top_urgent) * 2 + top_toxic) * 4 + fullness) * 2 + violation

    def toxic_port_state():
        can_place = Sorter.can_place_cargo(3)
        relation = Sorter.placement_relation(3)
        top_urgent = Sorter.top_is_next_exit(3)
        fullness = Sorter.fullness_state(3)
        violation = int(not Sorter.is_sorted(3)) ### Wrong order

        return (((can_place * 3 + relation) * 2 + top_urgent) * 4 + fullness) * 2 + violation

    def temp_port_state():
        can_place = Sorter.can_place_cargo(2)
        relation = Sorter.placement_relation(2)

        height = len(Sorter.ports[2])
        if height == 0:
            load = 0 ### Empty
        elif height == 1:
            load = 1 ### One container
        else:
            load = 2 ### Two or more containers

        return (can_place * 3 + relation) * 3 + load

    def get_current_state():
        incoming = Sorter.incoming_state()
        top_location = Sorter.top_location()

        port_1_state = Sorter.main_port_state(0)
        port_2_state = Sorter.main_port_state(1)

        Sorter.ports_swapped = port_2_state < port_1_state
        if Sorter.ports_swapped:
            port_1_state, port_2_state = port_2_state, port_1_state

        temp_state = Sorter.temp_port_state()
        toxic_state = Sorter.toxic_port_state()

        state = incoming
        state = state * 4 + top_location
        state = state * 192 + port_1_state
        state = state * 192 + port_2_state
        state = state * 18 + temp_state
        state = state * 96 + toxic_state

        return state
```

Durum uzayının bu kadar büyümesinin yarattığı problemleri azaltmak adına iki çözüme başvurulmuştur. Birincisi, 0'larla dolu büyük bir durum matrisi kullanmak yerine yalnızca görülmüş durumların bulunduğu bir dictionary kullanmaktır. Bu dictionary'de bulunmayan bir durumla karşılaşıldığında, o durum için sıfırlardan oluşan yeni bir Q-değerleri dizisi oluşturulmaktadır.

```
    def get_q_values(state): ### Get the Q-values for a state
        if state not in Sorter.q_table:
            Sorter.q_table[state] = np.zeros(Sorter.num_of_actions)
        return Sorter.q_table[state]

   ...

    def step(learn = False):
        old_state = Sorter.get_current_state()
        q_values = Sorter.get_q_values(old_state)
        
        if rnd.uniform(0, 1) < Sorter.epsilon:  ### Explore
            Sorter.action = rnd.randrange(Sorter.num_of_actions)
        else:                                   ### Exploit
            Sorter.action = np.argmax(q_values)

        reward = Sorter.act() ### Reward from the Sorter's action

        reward += Sorter.container_check() ### Reward from the current state of the ports
        Sorter.reward += reward

        terminated = (reward >= 200) ### Terminate if the sorting is complete

        if learn:
            if terminated:
                next_value = 0
            else:
                next_value = np.max(Sorter.get_q_values(Sorter.get_current_state()))

            Sorter.update_q_table(
                old_state=old_state,
                old_value=q_values[Sorter.action],
                next_value=next_value,
                reward=reward
            )

        return terminated
```
İkinci çözüm ise başlangıç durumunu rastgele shuffle kullanarak oluşturmak yerine, çözümü oluşturup legal adımlarla geriye doğru ilerleyerek başlangıç durumunu oluşturmaktır. Bu sayede çözülemez senaryolar elenmiş, oluşturulan senaryoların çözülebilir olması garanti edilmiş ve modelin daha verimli öğrenim yapabilmesi sağlanmıştır.

```
    def generate_scenario(): ### Generate a guaranteed possible scenario
        containers = list(range(Sorter.number_of_containers))
        for container in containers:
            if rnd.uniform(0, 1) < Sorter.toxic_chance:
                Sorter.toxic_containers.add(container)

        while len(Sorter.toxic_containers) > Sorter.toxic_port_capacity:
            Sorter.toxic_containers.remove(rnd.choice(list(Sorter.toxic_containers)))

        if Sorter.toxic_chance > 0 and len(Sorter.toxic_containers) == 0:
            Sorter.toxic_containers.add(rnd.choice(containers))

        regular_containers = [container for container in containers if not Sorter.is_toxic(container)]
        toxic_containers = [container for container in containers if Sorter.is_toxic(container)]

        final_ports = [[],[],[],[]]

        ### Build valid final ports
        regular_containers.sort(reverse = True)
        for container in regular_containers:
            possible_ports = []

            for port_id in [0,1]:
                if len(final_ports[port_id]) < Sorter.port_capacity:
                    possible_ports.append(port_id)

            port_id = rnd.choice(possible_ports)
            final_ports[port_id].append(container)

        toxic_containers.sort(reverse = True)
        for container in toxic_containers:
            final_ports[3].append(container)


        for port_id in [0,1,3]:
            sizes = []

            for _ in range(len(final_ports[port_id])):
                sizes.append(rnd.randrange(3))

            sizes.sort(reverse = True)

            for i in range(len(final_ports[port_id])):
                container = final_ports[port_id][i]
                Sorter.container_sizes[container] = sizes[i]

        Sorter.ports = [
            final_ports[0][:],
            final_ports[1][:],
            [],
            final_ports[3][:]
        ]

        ### Scramble the solution using legal moves ###
        reverse_move_count = rnd.randrange(10, 50)
        reverse_moves_done = 0
        attempt_count = 0
        last_move = None

        while reverse_moves_done < reverse_move_count and attempt_count < reverse_move_count * 20:
            moves = []
            for source_id in range(Sorter.total_port_count):
                if len(Sorter.ports[source_id]) == 0:
                    continue

                container = Sorter.ports[source_id][-1]

                for target_id in range(Sorter.total_port_count):
                    if source_id == target_id:
                        continue

                    ### Avoid immediately undoing the last random move
                    if last_move != None and source_id == last_move[1] and target_id == last_move[0]:
                        continue

                    if Sorter.can_place_to_port(container, target_id):
                        moves.append((source_id, target_id))

            if len(moves) == 0:
                last_move = None
                attempt_count += 1
                continue

            source_id, target_id = rnd.choice(moves)

            container = Sorter.ports[source_id].pop(-1)
            Sorter.ports[target_id].append(container)

            last_move = (source_id, target_id)
            reverse_moves_done += 1
            attempt_count += 1

        while True: ### Move everything back to the cargo
            possible_ports = []

            for port_id in range(Sorter.total_port_count):
                if len(Sorter.ports[port_id]) > 0:
                    possible_ports.append(port_id)

            if len(possible_ports) == 0:
                break

            port_id = rnd.choice(possible_ports)
            container = Sorter.ports[port_id].pop(-1)
            Sorter.cargo.insert(0, container)

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
        Sorter.get_q_values(old_state)[Sorter.action] = (1 - Sorter.learning_rate) * old_value + Sorter.learning_rate * (reward + Sorter.discount_factor * next_value)
```

Eylem seçimi için Epsilon Greedy algoritmasından yararlanılmaktadır. Bu algoritmada verilen bir _ε_ değerine göre model ya öğrendiği bilgiler arasından en optimal görünen eylemi seçer ya da rastgele eylemler gerçekleştirerek yeni bilgi edinmeye çalışır.

_ε_ : Epsilon [0.95 -> 0.01, Decay rate = 0.0025%]

```
        if rnd.uniform(0, 1) < Sorter.epsilon:  ### Explore
            Sorter.action = rnd.randrange(Sorter.num_of_actions)
        else:                                   ### Exploit
            Sorter.action = np.argmax(q_values)
```


## Eğitim Süreci ve Sonuçlar
Eğitim süreci sırasında yaşanan en büyük problem, yeni modelin karmaşıklığından dolayı eğitim sürecinin uzamasıdır. Yeni eklenen değişkenlerden ötürü modelin güncel versiyonu, önceki versiyon kadar hızlı öğrenememekte ve başarılı sonuçlar için daha fazla episode'a (bölüme) ihtiyaç duymaktadır. Buna rağmen yapılan optimizasyonlar sayesinde belirgin bir öğrenim gözlemlenebilmekte ve ödül grafiği tutarlı bir şekilde iyileşme göstermektedir.

<img width="1200" height="600" alt="Figure_1" src="https://github.com/user-attachments/assets/5cd72e59-be92-49ab-873f-4245ee0a3bef" />

<img width="1200" height="600" alt="Figure_2" src="https://github.com/user-attachments/assets/a3c10961-8fba-4d7f-be7b-e5912009af96" />
<p align="center">
<img width="700" height="400" alt="output1" src="https://github.com/user-attachments/assets/4fd12652-a666-4028-a36f-0e1305499783" />
<img width="700" height="400" alt="output2" src="https://github.com/user-attachments/assets/96487793-1614-468c-a21e-d7043e5f078c" />
<img width="700" height="400" alt="output3" src="https://github.com/user-attachments/assets/05aa98d1-027e-4396-8a67-6a4714c2f685" />
<img width="700" height="400" alt="output4" src="https://github.com/user-attachments/assets/a82fc993-ab92-4fbc-92e0-7b76711f97a0" />
<img width="700" height="400" alt="output5" src="https://github.com/user-attachments/assets/864e8b86-4a13-4d6e-ac56-cb160516b4bf" />
</p>





