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
        reward = 0

        ### If all the cargo are placed correctly
        if len(Sorter.cargo) == 0 and len(Sorter.ports[2]) == 0:
            if False not in [Sorter.is_sorted(n) and Sorter.is_size_sorted(n) and Sorter.is_toxic_sorted(n) for n in range(4)]:
                reward += 1000
        return reward
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
        elif not Sorter.can_stack_on_port(container, port_id):
            return False
        elif not Sorter.is_toxic(container) and port_id == 3: ### Don't allow normal containers into toxic port
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

<img width="340" height="400" alt="output1" src="https://github.com/user-attachments/assets/4fd12652-a666-4028-a36f-0e1305499783" />
<img width="700" height="400" alt="output2" src="https://github.com/user-attachments/assets/96487793-1614-468c-a21e-d7043e5f078c" />
<img width="700" height="400" alt="output3" src="https://github.com/user-attachments/assets/05aa98d1-027e-4396-8a67-6a4714c2f685" />
<img width="700" height="400" alt="output4" src="https://github.com/user-attachments/assets/a82fc993-ab92-4fbc-92e0-7b76711f97a0" />
<img width="700" height="400" alt="output5" src="https://github.com/user-attachments/assets/4809ed1a-e035-4784-bbc5-2fbbc1a4fd4a" />





